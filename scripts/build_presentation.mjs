import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root=path.resolve(process.env.DOCGUARD_ROOT || process.cwd()), out=path.join(root,'deliverables/submission');
const p=Presentation.create({slideSize:{width:1280,height:720}});
const navy='#142D4E', blue='#2563EB';
function text(s,t,x,y,w,h,size=28,color=navy,bold=false){const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=t;q.text.style={typeface:'Arial',fontSize:size,color,bold};return q;}
function slide(title,body,notes=''){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,'DOCGUARD   /   CS312B',64,30,1100,30,16,blue,true);text(s,title,64,98,1150,110,42,navy,true);if(body)text(s,body,64,236,1135,370,28);text(s,`KIET Deemed to be University                                          ${p.slides.items.length}`,64,674,1150,24,14,'#64748B');s.speakerNotes.text=notes;return s;}
let s=slide('DocGuard','Document tampering localization\nCNN and Transformer comparison\n\nDeep Learning and GenAI  |  CS312B\nB.Tech CS  |  Semester 5  |  Section D');
text(s,'Shrashti Agarwal  ·  2400290120240\nSaumya Tiwari  ·  2400240120230\nSubrat Singh  ·  2400290120250',660,422,555,145,21);
slide('The problem','A page label does not explain where an edit occurred.\n\nGoal: predict suspicious regions and make them reviewable.\n\nScope: controlled research on synthetic receipts.\nReal document detection accuracy is not established.');
s=slide('From document to review','Upload image or PDF  →  select page\n\nNormalize and resize  →  CNN or Transformer\n\nPixel scores  →  fixed validation threshold\n\nOverlay and heatmap  →  PNG, PDF and ZIP exports');
slide('A controlled synthetic dataset','600 fictional receipt sources → 1,200 images\n\n840 train  /  180 validation  /  180 test\nSource identities and layout configurations are disjoint.\n\nAuthentic and edited images share acquisition variation.\nMasks label edited rectangles, not individual characters.','Source: docs/DATASET.md and data/synthetic_v2. DocTamper was considered but not used.');
slide('Two segmentation approaches','Compact CNN\n30,081 parameters; local feature extraction and skip connections.\n\nMiT B0 Transformer plus custom multiscale decoder\n3,349,377 parameters; ImageNet pretrained encoder.\n\nCompared frozen encoder and full fine tuning. No GAN trained.','Architecture references: https://arxiv.org/abs/1505.04597 and https://arxiv.org/abs/2105.15203. Encoder: https://huggingface.co/nvidia/mit-b0. Custom decoder differs from official SegFormer head.');
slide('Training and fair evaluation','Three CPU epochs  |  160 × 200 input  |  batch 8  |  seed 42\n\nBinary cross entropy plus positive document Dice loss.\nCheckpoint and thresholds selected on validation data.\n\nGlobal pixel precision, recall, F1 and IoU on 180 test images.\nPlanned longer Colab training has not been executed.');
s=slide('Actual test results',null,'Sources: deliverables/model_comparison.json and runs/*/test_metrics.json. Global aggregate pixel metrics, not averaged per-image accuracy.');
const vals=[['Model','Precision','Recall','F1','IoU'],['CNN','0.1878','0.3565','0.2460','0.1403'],['Frozen Transformer','0.1330','0.6283','0.2195','0.1233'],['Fine tuned Transformer','0.1691','0.3538','0.2288','0.1292']];
const table=s.tables.add({rows:4,columns:5,left:64,top:245,width:1150,height:250,columnWidths:[430,180,180,180,180],values:vals});
for(let r=0;r<4;r++)for(let c=0;c<5;c++){const cell=table.getCell(r,c);cell.fill=r===0?navy:r%2?'#F1F5F9':'#FFFFFF';cell.text.style={typeface:'Arial',fontSize:23,bold:r===0,color:r===0?'#FFFFFF':navy};}
text(s,'The Transformer did not outperform CNN global pixel F1.',64,548,1150,70,28,blue,true);
slide('False positives are the main limitation','Authentic test pages incorrectly flagged\n\nCNN: 90 / 90  ·  100%\nFine tuned Transformer: 77 / 90  ·  85.6%\n\nFlag rule: at least 0.1% of model pixels predicted positive.\nHighlighted area is not a fraud probability.');
s=slide('Robustness under acquisition changes',null,'Source: deliverables/robustness/results.json. Fixed weights and thresholds, 180 images per condition per model. Screenshot proxy is simulated.');
s.images.add({blob:new Uint8Array(await fs.readFile(path.join(root,'deliverables/robustness/robustness.png'))),contentType:'image/png',position:{left:110,top:210,width:1060,height:365},fit:'contain',alt:'Measured CNN and Transformer robustness across six conditions'});
text(s,'JPEG, down and up resizing, and simulated screenshot acquisition.',64,600,1150,45,23);
s=slide('A working local review application',null);
s.images.add({blob:new Uint8Array(await fs.readFile(path.join(root,'deliverables/app_preview/01_workspace.png'))),contentType:'image/png',position:{left:80,top:202,width:1120,height:420},fit:'contain',alt:'DocGuard application upload and review workspace'});
slide('Regional language workflow','Interface: English, Hindi, Marathi, Tamil and Bengali.\n\nHindi PDF and regional language examples are included.\nLanguage switches preserve the current review.\n\nNo OCR or translation is performed.\nLanguage specific detection accuracy remains unvalidated.');
slide('Five minute demonstration','1. Analyse an edited English sample using CNN.\n2. Compare the Transformer overlay.\n3. Upload the supplied Hindi PDF.\n4. Switch interface language and export the review.\n5. Explain an authentic page false positive.','Use docs/TEAM_SETUP_AND_VIVA.md. Never interpret positive area as probability or present this prototype as certification.');
slide('Verification and reproducibility','14 unit checks passed.\n14 browser flows and 7 language checks passed.\n\nSource, trained weights, splits and metrics are supplied.\nCPU model forward medians: CNN 19.70 ms; Transformer 34.65 ms.\nThese timings exclude application and PDF processing.','Timing: CPU four threads, batch one, three warmups, twenty repetitions. Test evidence in deliverables/app_preview.');
slide('What the project establishes','A reproducible CNN and Transformer experiment.\nA complete local document review workflow.\nA clear account of weak detection performance.\n\nNext: licensed real documents, higher resolution,\nlonger training and independent calibration.','References: https://arxiv.org/abs/1505.04597 ; https://arxiv.org/abs/2105.15203 ; https://huggingface.co/nvidia/mit-b0 . Repository https://github.com/Shrashti1234/Docguard. Proposed improvements are not measured results.');
await fs.mkdir(out,{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(root,`tmp/submission/slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
const draft=path.join(root,'tmp/submission/candidate.pptx');await(await PresentationFile.exportPptx(p)).save(draft);
const skill='C:/Users/Asus/.codex/plugins/cache/openai-primary-runtime/presentations/26.1022.11436/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs'));
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:path.join(out,'DocGuard_Assessment.pptx'),pythonExecutable:'C:/Users/Asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','7'],requiredNativeTableOwnerSlides:[7],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(root,'tmp/submission/validation-final.json')});
console.log(JSON.stringify(result));





