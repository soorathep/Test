"""Freeze reviewed real-screen captures against exact narration sentence starts."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
script=json.loads((ROOT/'narration.json').read_text())
selections={
1:[('01-lab-entry.png',None,'Open the published Lab 01'),('02-ideal-baseline.png','We will study one synthetic','One ideal synthetic mixture')],
2:[('02-ideal-baseline.png',None,'Select synthetic system and ideal liquid'),('04-boundaries-and-inputs.png','Enter three hundred fifty','Enter T, P, and feed composition'),('05-pxy-and-results.png','At this temperature','Synthetic property record at 350 K')],
3:[('03-predict-pressure.png',None,'Predict pressure effects before trying them')],
4:[('05-pxy-and-results.png',None,'Read the pressure-composition diagram'),('04-boundaries-and-inputs.png','Look at the two boundary','Different specified compositions at the boundaries')],
5:[('02-ideal-baseline.png',None,'Read the baseline phase and compositions'),('05-pxy-and-results.png','The horizontal tie line','Connect the coexisting compositions')],
6:[('06-balance-interpretation.png',None,'Check both component balances on one mole of feed')],
7:[('07-rachford-rice.png',None,'Find the vapor fraction at the Rachford-Rice root'),('05-pxy-and-results.png','Return the Diagram menu','Return to P-x-y before exporting')],
8:[('08-label-baseline.png',None,'Give the calculated baseline a useful label'),('08-export-baseline.png','Return to the experiment export','Export the full calculated study'),('08-baseline-comparison.png','The case label helps','Locate the saved baseline result'),('08-label-baseline.png','Download current inputs only','Distinguish setup-only files from calculated studies')],
9:[('09-input-110.png',None,'Change only pressure to 110 kPa'),('09-liquid-110.png','The pressure is above','Interpret liquid-only result and absent vapor'),('09-label-110.png','In the workspace, enter','Label the high-pressure case'),('09-export-110.png','Select Export experiment to capture','Save the calculated high-pressure study')],
10:[('10-input-80.png',None,'Change only pressure to 80 kPa'),('10-vapor-80.png','Eighty kilopascals is below','Interpret vapor-only result and absent liquid'),('10-label-80.png','Label this case Low pressure','Label the low-pressure case'),('10-export-80.png','The workspace should now hold','Save the third calculated study')],
11:[('11-comparison-inputs.png',None,'Compare the three recorded input sets'),('11-comparison-results.png','The comparison displays','Compare phase amounts and absent compositions'),('11-comparison-units.png','Also inspect the pressure units','Distinguish input kPa from result Pa'),('11-curve-export.png','Use Curve CSV','Download the selected equilibrium curve'),('05-pxy-and-results.png','Because temperature and the ideal','Distinguish fixed curves from the changing flash state')],
12:[('12-download-comparison.png',None,'Save the three-case comparison JSON'),('12-cleared-comparison.png','For this demonstration, Clear comparison','Clear only the saved synthetic cases in this tab'),('12-reopened-cases.png','Now use Load studies','Load the downloaded comparison'),('12-restored-inputs.png','Choose Restore beside','Restore the 95 kPa controls'),('12-recalculated-controls.png','Check the system, ideal model','Run Calculate equilibrium again'),('12-recalculated-baseline.png','Verify that the fresh result','Verify the freshly recalculated baseline')],
13:[('13-before-independent-attempt.png',None,'Keep the baseline visible while attempting a new pressure on paper')],
14:[('14-independent-result.png',None,'Check the 90 kPa result after the independent attempt'),('14-input-90.png','From the ideal bubble relation','Check substitutions using the 90 kPa controls'),('14-independent-balance.png','Component A contributes','Check both component balances')]
}
scenes=[]
for n,items in selections.items():
    for file,prefix,label in items:
        if prefix is None: prefix=script[n-1]['narration'].split('.')[0]+'.'
        scenes.append({'slide':n,'file':file,'sentence_prefix':prefix,'label':label,'sha256':hashlib.sha256((ROOT/'demo-frames'/file).read_bytes()).hexdigest()})
(ROOT/'demo-scenes.json').write_text(json.dumps({'capture_url':'https://www.skhgroup.net/teaching/2105603/labs/#experiment','capture_date':'2026-10-20','capture_viewport':[1280,720],'scenes':scenes},ensure_ascii=False,indent=2)+'\n')
print(f'{len(scenes)} scene placements in {len(selections)} chapters')
