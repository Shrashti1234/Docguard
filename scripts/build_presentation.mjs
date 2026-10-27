import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root=path.resolve(process.env.DOCGUARD_ROOT || process.cwd());
const dir=path.join(root,'tmp/redesign');await fs.mkdir(dir,{recursive:true});
const out=path.join(root,'deliverables/submission');
const p=Presentation.create({slideSize:{width:1280,height:720}});
p.theme.defaultFont='Arial';
const C={ink:'#11283F',paper:'#F6F4EF',blue:'#2764C5',muted:'#5C6B78',white:'#FFFFFF',mint:'#91DBCB',red:'#B75440'};
function tx(s,t,x,y,w,h,size=26,color=C.ink,bold=false){let a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={typeface:'Arial',fontSize:size,color,bold};return a;}
function box(s,x,y,w,h,fill){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function slide(title,sub='',dark=false){let s=p.slides.add();s.background.fill=dark?C.ink:C.paper;s.speakerNotes.text='DocGuard, CS312B, KIET Deemed to be University. All measurements are preliminary synthetic dataset results. Source: local experiment artifacts.';tx(s,'DOCGUARD',56,30,300,30,16,dark?C.mint:C.blue,true);tx(s,String(p.slides.items.length).padStart(2,'0'),1160,30,70,30,16,dark?C.mint:C.muted);if(title)tx(s,title,56,90,1170,100,44,dark?C.white:C.ink,true);if(sub)tx(s,sub,56,185,1160,65,22,dark?'#BBCBD7':C.muted);return s;}
async function img(s,file,x,y,w,h){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(root,file))),contentType:'image/png',position:{left:x,top:y,width:w,height:h},fit:'contain',alt:file});}
function note(s,t){s.speakerNotes.text=t;}
function big(s,num,label,x,y,w=340,dark=false){tx(s,num,x,y,w,105,76,dark?C.mint:C.blue,true);tx(s,label,x,y+115,w,75,23,dark?C.white:C.ink);}
let s=slide('', '',true);
tx(s,'KIET Deemed to be University',56,104,690,35,22,'#BBCBD7');
tx(s,'DocGuard',56,170,740,125,94,C.white,true);
tx(s,'Document tampering\nlocalization',62,310,690,145,43,C.white);
tx(s,'CNN and Transformer comparison',62,478,690,45,27,C.mint);
tx(s,'Deep Learning and GenAI · CS312B\nB.Tech CS · Semester 5 · Section D',62,598,700,66,20,'#BBCBD7');
await img(s,'data/synthetic_v2/images/00510_tampered.png',860,110,295,400);
tx(s,'Synthetic receipt used in the experiment',815,528,390,45,17,'#BBCBD7');
note(s,'Introduce the team and project. This is a research prototype using synthetic documents. No production fraud detection claim.');
s=slide('The team','Deep Learning and GenAI · CS312B');
const members=[['Shrashti Agarwal','2400290120240'],['Saumya Tiwari','2400240120230'],['Subrat Singh','2400290120250']];
members.forEach(([n,r],i)=>{const y=282+i*116;tx(s,n,65,y,730,55,37,C.ink,true);tx(s,r,860,y+5,345,45,27,C.blue);});
tx(s,'KIET Deemed to be University  /  B.Tech CS  /  Semester 5  /  Section D',65,655,1150,35,20,C.muted);
s=slide('Where did the document change?','The review needs a location, not just a page label.');
await img(s,'data/synthetic_v2/images/00511_authentic.png',70,270,345,360);
await img(s,'data/synthetic_v2/images/00511_tampered.png',475,270,345,360);
tx(s,'Original',160,642,230,40,22,C.muted,true);tx(s,'Edited',590,642,230,40,22,C.blue,true);
tx(s,'Task',920,288,250,40,22,C.blue,true);tx(s,'Predict a mask\nfor suspicious\nregions.',920,345,300,145,32,C.ink,true);tx(s,'Controlled study on\nfictional receipts.',920,525,300,80,22,C.muted);
s=slide('The review pipeline','A local workflow from upload to downloadable evidence.');
const steps=[['01','Document','Image or PDF\nSelected page'],['02','Preprocess','Normalize\n160 × 200'],['03','Segment','CNN or MiT B0\nPixel scores'],['04','Review','Overlay and heatmap\nPNG · PDF · ZIP']];
steps.forEach(([n,t,b],i)=>{const x=60+i*307;tx(s,n,x,295,230,95,68,C.blue,true);tx(s,t,x,410,275,55,32,C.ink,true);tx(s,b,x,480,275,100,24,C.muted);if(i<3)tx(s,'→',x+240,330,60,60,40,C.blue);});
note(s,'Inference runs on local CPU. Thresholds were selected on validation data and fixed during test evaluation. Predicted area is not a fraud probability.');
s=slide('1,200 images. One controlled benchmark.','600 fictional source receipts, each with an authentic and edited version.');
big(s,'840','Training images',65,290);big(s,'180','Validation images',465,290);big(s,'180','Test images',865,290);
tx(s,'Source identities and layout configurations are disjoint across splits.',65,530,1140,60,29,C.ink,true);
tx(s,'Four fonts · six editable fields · rectangular edit masks\nJPEG and blur acquisition variation applied to both labels',65,610,1140,75,22,C.muted);
s=slide('Two routes to a pixel mask','The same data split and output task; different feature extractors.');
tx(s,'Compact CNN',60,280,530,55,36,C.blue,true);tx(s,'MiT B0 Transformer',690,280,530,55,36,C.blue,true);
tx(s,'30,081',60,360,530,95,70,C.ink,true);tx(s,'3,349,377',690,360,530,95,70,C.ink,true);
tx(s,'parameters',65,458,500,40,22,C.muted);tx(s,'parameters',695,458,500,40,22,C.muted);
tx(s,'Local feature extraction\nEncoder and decoder with skip connections',65,530,540,100,25);tx(s,'ImageNet pretrained encoder\nCustom multiscale binary decoder',695,530,530,100,25);
note(s,'CNN inspired by U-Net, not the full original U-Net. Transformer uses nvidia/mit-b0 with a custom decoder, not an untouched official SegFormer head. Frozen and full fine tuning were evaluated. References: https://arxiv.org/abs/1505.04597 ; https://arxiv.org/abs/2105.15203 ; https://huggingface.co/nvidia/mit-b0 . No GAN was trained.');
s=slide('Training kept the comparison controlled','Preliminary CPU runs on a laptop.');
big(s,'3','Epochs per model',60,275,330);big(s,'160 × 200','Input width × height',445,275,410);big(s,'8','Batch size',940,275,230);
tx(s,'Binary cross entropy + positive document Dice loss',65,535,1140,50,30,C.ink,true);
tx(s,'Seed 42 · checkpoint and thresholds selected on validation data\nLonger, higher resolution Colab experiments are planned, not executed.',65,600,1150,80,23,C.muted);
s=slide('CNN led the preliminary pixel F1 results','Higher is better. Global metrics on 180 held out test images.');
s.charts.add('bar',{position:{left:60,top:270,width:740,height:355},categories:['CNN','Frozen Transformer','Fine tuned Transformer'],series:[{name:'Pixel F1',values:[.2460,.2195,.2288],fill:C.blue}],hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:85},xAxis:{min:0,max:.3,numberFormatCode:'0.00',textStyle:{fontSize:18,fill:C.muted}},yAxis:{min:0,max:.3,numberFormatCode:'0.00',textStyle:{fontSize:18,fill:C.ink}} ,dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0000',textStyle:{fontSize:20,fill:C.ink,bold:true}},chartFill:C.paper,plotAreaFill:C.paper});
tx(s,'0.2460',870,300,360,110,72,C.blue,true);tx(s,'Best pixel F1\nCompact CNN',875,422,335,95,28,C.ink,true);tx(s,'Pretraining alone did not\nimprove this experiment.',875,555,335,90,23,C.muted);
note(s,'Actual global pixel F1 values: CNN 0.2460103262, frozen Transformer 0.2194730745, full fine tuned Transformer 0.2288149574. Source deliverables/model_comparison.json. Native editable chart.');
s=slide('False positives remain the main barrier','Authentic pages incorrectly flagged by the current document rule.',true);
big(s,'90 / 90','CNN · 100% false flags',65,285,550,true);big(s,'77 / 90','Fine tuned Transformer · 85.6%',690,285,540,true);
tx(s,'Flag rule: predicted foreground ≥ 0.1% of the model grid.',65,555,1130,55,27,C.white);
tx(s,'Highlighted area is not a fraud probability.',65,620,1140,45,27,C.mint,true);
s=slide('The evidence behind the comparison','Precision, recall and IoU explain the weak localization results.');
const values=[['Model','Precision','Recall','F1','IoU'],['CNN','0.1878','0.3565','0.2460','0.1403'],['Frozen Transformer','0.1330','0.6283','0.2195','0.1233'],['Fine tuned Transformer','0.1691','0.3538','0.2288','0.1292']];
let tb=s.tables.add({rows:4,columns:5,left:60,top:275,width:1160,height:270,columnWidths:[440,180,180,180,180],values});
for(let r=0;r<4;r++)for(let c=0;c<5;c++){let cell=tb.getCell(r,c);cell.fill=r===0?C.ink:r%2?'#E7EDF1':C.white;cell.text.style={typeface:'Arial',fontSize:23,color:r===0?C.white:C.ink,bold:r===0};}
tx(s,'Low precision means many highlighted pixels are false positives.',65,595,1140,70,29,C.red,true);
note(s,'Source runs/*/test_metrics.json and deliverables/model_comparison.json. Aggregate pixel counts, not per-image averaged accuracy.');
s=slide('Robustness across six conditions','Fixed weights and validation thresholds; high false positives remain.');
await img(s,'deliverables/robustness/robustness.png',50,265,1180,355);
tx(s,'The screenshot condition is simulated. Small F1 gains do not establish reliability.',65,645,1150,45,22,C.muted);
s=slide('A complete document review workspace','Image and PDF upload · model comparison · exportable review evidence');
await img(s,'deliverables/app_preview/02_transformer_result.png',55,255,900,410);
tx(s,'Local CPU',990,285,240,45,29,C.blue,true);tx(s,'Overlay\nHeatmap\nSide by side',990,365,240,150,27);tx(s,'PNG\nPDF\nReview ZIP',990,540,240,120,24,C.muted);
s=slide('Regional languages in one review','The current document and results stay available when the interface switches.');
await img(s,'deliverables/app_preview/06_hindi_interface.png',60,260,760,390);
tx(s,'English\nHindi\nMarathi\nTamil\nBengali',880,270,340,255,34,C.ink,true);
tx(s,'Hindi PDF examples included.\nNo OCR or translation.\nLanguage accuracy is unvalidated.',880,555,335,125,21,C.muted);
s=slide('Demonstration and next steps','A reproducible project with a measured, clearly stated limitation.',true);
tx(s,'Live demonstration',65,280,540,55,32,C.mint,true);tx(s,'Analyse an edited receipt\nCompare both model overlays\nUpload a Hindi PDF and export\nExplain an authentic false positive',65,365,560,200,27,C.white);
tx(s,'Next experiments',700,280,500,55,32,C.mint,true);tx(s,'Licensed real documents\nHigher resolution and longer training\nIndependent calibration\nReal camera and scanner evaluation',700,365,520,200,27,C.white);
tx(s,'14 unit checks passed · 14 browser flows · 7 language checks',65,635,1140,45,23,'#BBCBD7');
note(s,'These are proposed next steps, not achieved improvements. CPU forward medians: CNN 19.70 ms and Transformer 34.65 ms, four threads, batch one, three warmups and twenty repeats; not end to end app timings. Repository https://github.com/Shrashti1234/Docguard. Architecture references https://arxiv.org/abs/1505.04597 and https://arxiv.org/abs/2105.15203 .');
for(let i=0;i<p.slides.items.length;i++){let b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(dir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
let candidate=path.join(dir,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const skill='C:/Users/Asus/.codex/plugins/cache/openai-primary-runtime/presentations/26.1022.11436/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs'));
let res=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(out,'DocGuard_Professional_Final.pptx'),pythonExecutable:'C:/Users/Asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','10'],requiredNativeTableOwnerSlides:[10],requiredNativeChartOwnerSlides:[8],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation-final.json')});console.log(JSON.stringify({final:res.finalPath,slides:p.slides.items.length}));


