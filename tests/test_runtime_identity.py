"""Una revisione non può rinominare codice vecchio dopo un edit a caldo."""
import json
import http.client
import os
from pathlib import Path
import shutil
import select
import subprocess
import sys

import pytest

from kirchhoff.runtime_identity import SourceSnapshot, RuntimeIdentityError


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('change', ['edit','add','remove','unreadable'])
def test_snapshot_refuses_dependency_drift_and_stays_latched(tmp_path, monkeypatch, change):
    file=tmp_path/'engine.py';file.write_text('value = 1\n')
    snapshot=SourceSnapshot(tmp_path)
    first=snapshot.revision(['engine.py'])
    assert first == snapshot.revision(['engine.py'])
    if change=='edit':file.write_text('value = 2\n')
    elif change=='add':(tmp_path/'new.py').write_text('value = 3\n')
    elif change=='remove':file.unlink()
    else:
        real=Path.read_bytes
        def denied(path):
            if path==file:raise PermissionError('unreadable')
            return real(path)
        monkeypatch.setattr(Path,'read_bytes',denied)
    with pytest.raises(RuntimeIdentityError,match='Riavvia'):
        snapshot.revision(['engine.py'])
    monkeypatch.undo()
    file.write_text('value = 1\n')
    if (tmp_path/'new.py').exists():(tmp_path/'new.py').unlink()
    with pytest.raises(RuntimeIdentityError,match='Riavvia'):
        snapshot.assert_current()


def test_snapshot_rejects_empty_sources_and_path_escape(tmp_path):
    with pytest.raises(RuntimeIdentityError,match='non disponibili'):
        SourceSnapshot(tmp_path)
    (tmp_path/'engine.py').write_text('value = 1\n')
    snapshot=SourceSnapshot(tmp_path)
    with pytest.raises(ValueError):snapshot.revision(['../outside.py'])
    with pytest.raises(KeyError):snapshot.revision(['unknown.py'])
    with pytest.raises(TypeError):snapshot._sources['engine.py']=b'changed'


def test_launcher_outside_package_is_guarded_without_relabeling_revision(tmp_path):
    package=tmp_path/'package';package.mkdir()
    (package/'engine.py').write_text('value = 1\n')
    launcher=tmp_path/'server.py';launcher.write_text('serve = 1\n')
    snapshot=SourceSnapshot(package)
    first=snapshot.revision(['engine.py'])
    snapshot.register_entrypoint(launcher)
    assert first==snapshot.revision(['engine.py'])
    launcher.write_text('serve = 2\n')
    with pytest.raises(RuntimeIdentityError,match='Riavvia'):snapshot.assert_current()


def _isolated_package(tmp_path):
    target=tmp_path/'installed'/'kirchhoff'
    shutil.copytree(ROOT/'src'/'kirchhoff',target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    return target


@pytest.mark.parametrize('before_first_ac', [False,True])
def test_real_subprocess_rejects_lazy_ac_drift_and_pdf_without_checkout(tmp_path,before_first_ac):
    target=_isolated_package(tmp_path)
    code=r'''
import json
from pathlib import Path
import kirchhoff
from kirchhoff.pipeline.lesson import create_lesson, lesson_build
from kirchhoff.pipeline.lesson_pdf import export_pdf
from kirchhoff.runtime_identity import RuntimeIdentityError
text='@ac 2 rad/s\nV1 a 0 4 volt 0deg\nR1 a 0 2 ohm\n? current R1'
first=lesson_build()
lesson=None if BEFORE else create_lesson(text,source_sha='0'*40)
dependency=Path(kirchhoff.__file__).parent/'pipeline'/'lesson_ac.py'
dependency.write_bytes(dependency.read_bytes()+b'\n# changed after process start\n')
failed=[]
for name,action in [('solve',lambda:create_lesson(text,source_sha='0'*40)),('build',lesson_build),('pdf',lambda:export_pdf(lesson or {'outcome':'solved'}))]:
 try:action()
 except RuntimeIdentityError as exc:failed.append(name);assert 'Riavvia' in str(exc)
 else:raise AssertionError(name+' exposed stale result')
print(json.dumps({'failed':failed,'first_build':first,'had_previous_lesson':lesson is not None}))
'''.replace('BEFORE',repr(before_first_ac))
    env={**os.environ,'PYTHONPATH':str(target.parent),'PYTHONDONTWRITEBYTECODE':'1'}
    result=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env=env,text=True,capture_output=True,timeout=40)
    assert result.returncode==0,result.stderr
    output=json.loads(result.stdout)
    assert output['failed']==['solve','build','pdf']
    assert output['had_previous_lesson'] is (not before_first_ac)


def test_changes_before_first_lesson_are_caught_even_before_pipeline_import(tmp_path):
    target=_isolated_package(tmp_path)
    code=r'''
from pathlib import Path
import kirchhoff
from kirchhoff.runtime_identity import RuntimeIdentityError
dependency=Path(kirchhoff.__file__).parent/'domain'/'exact.py'
dependency.write_bytes(dependency.read_bytes()+b'\n# changed before first lesson import\n')
from kirchhoff.pipeline.lesson import create_lesson
try:create_lesson('V1 a 0 2 volt\nR1 a 0 2 ohm\n? current R1',source_sha='0'*40)
except RuntimeIdentityError:print('refused')
else:raise AssertionError('late snapshot accepted changed kernel')
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env={**os.environ,'PYTHONPATH':str(target.parent)},text=True,capture_output=True,timeout=40)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='refused'


@pytest.mark.parametrize('dependency', ['pipeline/lesson_ac.py','domain/exact.py','render/layout/connected.py','pipeline/lesson_pdf_math.py','entrypoint'])
def test_http_subprocess_start_edit_refuse_and_restart_on_isolated_copy(tmp_path,dependency):
    project=tmp_path/'project';package=project/'src'/'kirchhoff'
    shutil.copytree(ROOT/'src'/'kirchhoff',package,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    launcher=project/'scripts'/'serve_student.py';launcher.parent.mkdir()
    shutil.copyfile(ROOT/'scripts'/'serve_student.py',launcher)
    runner=r'''
import importlib.util, sys
spec=importlib.util.spec_from_file_location('isolated_student',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
server=module.ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
print(server.server_port,flush=True)
server.serve_forever()
'''
    # Lo SHA zero descrive soltanto la fixture, mai una release o il checkout.
    env={**os.environ,'KIRCHHOFF_SOURCE_SHA':'0'*40,'PYTHONDONTWRITEBYTECODE':'1'}
    def start():
        process=subprocess.Popen([sys.executable,'-u','-c',runner,str(launcher)],cwd=tmp_path,env=env,
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        ready=select.select([process.stdout],[],[],15)[0]
        if not ready:
            process.terminate();output=process.communicate(timeout=10)
            pytest.fail('Server isolato non pronto: '+repr(output))
        line=process.stdout.readline().strip()
        if not line:
            process.terminate();output=process.communicate(timeout=10)
            pytest.fail('Avvio HTTP fallito: '+repr(output))
        return process,int(line)
    def request(port,path,netlist=None):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
        if netlist is None:connection.request('GET',path)
        else:connection.request('POST',path,json.dumps(dict(netlist=netlist)),{'Content-Type':'application/json'})
        response=connection.getresponse();data=response.read();status=response.status;connection.close()
        return status,json.loads(data)
    text='@ac 2 rad/s\nV1 a 0 4 volt 0deg\nR1 a 0 2 ohm\n? current R1'
    process,port=start()
    try:
        # Prima chiamata DC: il modulo AC può non essere ancora stato caricato.
        status,before=request(port,'/api/solve','V1 a 0 4 volt\nR1 a 0 2 ohm\n? current R1')
        assert status==200 and before['outcome']=='solved'
        edited=launcher if dependency=='entrypoint' else package/dependency
        edited.write_bytes(edited.read_bytes()+b'\n# runtime identity mutation in isolated fixture\n')
        for route in ('/api/solve','/api/pdf','/api/capabilities'):
            status,body=request(port,route,None if route.endswith('capabilities') else text)
            assert status==409 and body['code']=='runtime_changed'
            assert 'Riavvia' in body['message'] and 'answer' not in body and 'verification' not in body
    finally:
        process.terminate();process.communicate(timeout=10)
    # Il processo successivo acquisisce i nuovi byte ed è nuovamente utilizzabile.
    process,port=start()
    try:
        status,after=request(port,'/api/solve','V1 a 0 4 volt\nR1 a 0 2 ohm\n? current R1')
        assert status==200 and after['outcome']=='solved'
        assert after['source_sha']=='0'*40
        if dependency!='entrypoint':
            assert before['lesson_build']!=after['lesson_build']
        else:
            assert before['lesson_build']==after['lesson_build']
        status,ac=request(port,'/api/solve',text)
        assert status==200 and ac['outcome']=='solved'
    finally:
        process.terminate();process.communicate(timeout=10)
