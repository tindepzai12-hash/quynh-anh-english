import * as THREE from 'three';

export const STUDIO_MODEL_URL='/assets/justin-mini/studio-v39/JustinMini.glb';
export const STUDIO_VERSION='v39-vest22';
export const VEST_PREFERENCE='justin-studio-sailor-vest';

export function studioBounds(model){
 model.updateMatrixWorld(true);
 const bounds=new THREE.Box3();
 model.traverse(o=>{if(o.isSkinnedMesh&&o.visible&&o.material.name.includes('Original-PBR')){o.skeleton.update();bounds.expandByObject(o,true);}});
 return bounds;
}

// The new body is one welded surface. Interaction landmarks no longer depend
// on the separate head/belly meshes used by the retired model.
export function studioLandmark(model,part){
 model.updateMatrixWorld(true);
 if(part==='mouth'){
  const tooth=model.getObjectByName('GEO-Justin-ToothTrial');
  if(tooth){tooth.skeleton?.update();const box=new THREE.Box3().setFromObject(tooth,true);return box.getCenter(new THREE.Vector3()).add(new THREE.Vector3(0,-.07,.06));}
 }
 const box=studioBounds(model),size=box.getSize(new THREE.Vector3());
 const p=box.getCenter(new THREE.Vector3());
 p.y=box.min.y+size.y*(part==='body'?.35:.89);
 const ray=new THREE.Raycaster(new THREE.Vector3(p.x,p.y,box.max.z+1),new THREE.Vector3(0,0,-1));
 const hit=ray.intersectObject(model,true).find(h=>h.object.visible&&h.object.material?.name.includes('Original-PBR'));
 p.z=hit?hit.point.z:box.max.z;
 return p;
}

export function savedVest(){try{return localStorage.getItem(VEST_PREFERENCE)!=='off';}catch{return true;}}
export function saveVest(on){try{localStorage.setItem(VEST_PREFERENCE,on?'on':'off');}catch{}}
