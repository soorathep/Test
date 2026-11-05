"""Review all Week5 narration with cached local ASR and exact source hashes.

This is an automated intelligibility screen, not a full subjective listening
review. It never downloads a model and never substitutes ASR for science review.
Run with the absolute research interpreter.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.metadata, json, math
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'outputs/week05-video'
CACHE=OUT/'asr-cache'
SCRIPT=HERE/'narration.json'
WAVS=OUT/'audio'
SETTINGS={'model':'tiny.en','device':'cpu','compute_type':'int8','cpu_threads':1,'num_workers':1,'beam_size':3,'language':'en','local_files_only':True}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    entries=json.loads(SCRIPT.read_text())
    assert [r['slide'] for r in entries]==list(range(1,33))
    sourcehash=sha(SCRIPT)
    settings={**SETTINGS,'faster_whisper_version':importlib.metadata.version('faster-whisper')}
    sh=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()
    CACHE.mkdir(parents=True,exist_ok=True)
    manifestpath=WAVS/'manifest.json'
    manifest=json.loads(manifestpath.read_text()) if manifestpath.exists() else None
    reviewpath=HERE/'qa-audio-review-decisions.json'
    reviews=json.loads(reviewpath.read_text()) if reviewpath.exists() else {}
    results=[];model=None;pending=[]
    for entry in entries:
        num=entry['slide'];wav=WAVS/f'segment-{num:02d}.wav'
        if not wav.exists():pending.append(num);continue
        wavhash=sha(wav);cache=CACHE/f'{wavhash}-{sh[:12]}.json'
        if cache.exists():result=json.loads(cache.read_text())
        else:
            signal,rate=sf.read(wav);assert signal.ndim==1
            gcd=math.gcd(rate,16000);pcm=resample_poly(signal,16000//gcd,rate//gcd).astype(np.float32)
            if model is None:
                model=WhisperModel('tiny.en',device='cpu',compute_type='int8',cpu_threads=1,num_workers=1,download_root=str(ROOT/'tmp/audio/whisper-model'),local_files_only=True)
            segments,info=model.transcribe(pcm,language='en',beam_size=3)
            segments=[{'start':s.start,'end':s.end,'text':s.text.strip()} for s in segments]
            assert sha(wav)==wavhash
            result={'audio_sha256':wavhash,'settings':settings,'recognized':' '.join(s['text'] for s in segments),'segments':segments,'duration_seconds':len(signal)/rate}
            cache.write_text(json.dumps(result,indent=2)+'\n')
        entryhash=hashlib.sha256(entry['narration'].encode()).hexdigest()
        if manifest:
            assert manifest[num-1]['audio_sha256']==wavhash and manifest[num-1]['narration_sha256']==entryhash
        row={'slide':num,'title':entry['title'],'audio_sha256':wavhash,'narration_sha256':entryhash,'source':entry['narration'],'asr':result['recognized'],'cache':str(cache.relative_to(ROOT))}
        prior=reviews.get(str(num),{})
        if prior.get('audio_sha256')==wavhash and prior.get('narration_sha256')==entryhash:
            row['source_comparison']=prior
        results.append(row)
        assert sha(SCRIPT)==sourcehash
        report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':sourcehash,'scope':'All 32 English narration tracks','method':settings,'status':'pending_source_comparison','pending_audio':pending+[i for i in range(num+1,33)],'checks':results,'full_subjective_listening_review_performed':False,'limitations':['Tiny ASR may misrecognize scientific names, letters and spoken decimals.','Hash-bound source comparison checks probable meaning, not complete subjective audio quality.']}
        (OUT/'asr-review.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'ASR slide{num:02d}: {result["duration_seconds"]:.1f}s',flush=True)
    report['pending_audio']=pending
    reviewed=sum('source_comparison' in r for r in results)
    report['reviewed_track_count']=reviewed
    report['status']='complete_source_comparison' if reviewed==32 and not pending else 'pending_source_comparison'
    report['passed']=report['status']=='complete_source_comparison'
    report['decision_file_sha256']=sha(reviewpath) if reviewpath.exists() else None
    (OUT/'asr-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Completed {len(results)}tracks; pending {pending}',flush=True)
if __name__=='__main__': main()
