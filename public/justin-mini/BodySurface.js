import * as THREE from 'three';
import {studioBounds,studioLandmark} from './StudioModel.js?v=39';

export function visibleInTree(o){for(;o;o=o.parent)if(!o.visible)return false;return true;}
export function classifyFace(x,y){
 if(y>.78)return 'forehead';
 if(y<.14&&Math.abs(x-.5)<.2)return 'chin';
 if(Math.abs(x-.5)<.12&&y<.42&&y>.22)return 'nose';
 return x<.5?'left-cheek':'right-cheek';
}
// Triangle barycentrics keep a mark on the animated surface, including skinning.
export class SurfaceAnchor {
 constructor(hit){this.object=hit.object;this.face=hit.face;this.fallback=hit.object.worldToLocal(hit.point.clone());this.bary=new THREE.Vector3(1,0,0);
  if(this.face){const [a,b,c]=this.vertices();const p=hit.object.worldToLocal(hit.point.clone());THREE.Triangle.getBarycoord(p,a,b,c,this.bary);}}
 vertices(){return ['a','b','c'].map(k=>this.object.getVertexPosition(this.face[k],new THREE.Vector3()));}
 world(){if(!this.face)return this.object.localToWorld(this.fallback.clone());const [a,b,c]=this.vertices();return this.object.localToWorld(a.multiplyScalar(this.bary.x).addScaledVector(b,this.bary.y).addScaledVector(c,this.bary.z));}
 normal(){if(!this.face)return new THREE.Vector3(0,0,1);const [a,b,c]=this.vertices();return b.sub(a).cross(c.sub(a)).normalize().transformDirection(this.object.matrixWorld);}
 restPoint(){if(!this.face)return this.fallback.clone();const p=this.object.geometry.attributes.position;return ['a','b','c'].reduce((v,k,i)=>v.addScaledVector(new THREE.Vector3().fromBufferAttribute(p,this.face[k]),this.bary.getComponent(i)),new THREE.Vector3());}
}
export class BodySurface {
 constructor(controller){this.c=controller;this.ray=new THREE.Raycaster();this.ndc=new THREE.Vector2();}
 update(){this.c.model.updateMatrixWorld(true);this.c.model.traverse(o=>{if(o.isSkinnedMesh&&visibleInTree(o)){o.skeleton.update();o.computeBoundingSphere();}});}
 hits(ray){this.update();return ray.intersectObject(this.c.model,true).filter(h=>visibleInTree(h.object));}
 region(hit){const n=hit.object.name;if(this.c.studioModel){if(/Tooth|Tongue/.test(n))return 'mouth';if(hit.object.material?.name.includes('Sailor-'))return 'belly';const box=studioBounds(this.c.model),f=box.getParameter(hit.point,new THREE.Vector3());if(f.y<.54)return 'belly';if(f.y>.87)return 'forehead';return classifyFace(f.x,(f.y-.54)/.34);}if(/Forelock|Hair/.test(n))return 'hair';if(/Belly|Torso|Body|Outfit_/.test(n))return 'belly';if(/Hand|Arm/.test(n))return 'hand';if(/Mouth|Tongue|Tooth/.test(n))return 'mouth';if(/Nostril|Muzzle|Nose/.test(n))return 'nose';
 const head=this.c.model.getObjectByName('Retopology_Head');if(/Head|Eye|Brow|Lid|Pupil/.test(n)&&head){const p=head.worldToLocal(hit.point.clone());head.geometry.computeBoundingBox();const b=head.geometry.boundingBox;const f=b.getParameter(p,new THREE.Vector3());return classifyFace(f.x,f.y);}return 'body';}
 pick(x,y){const r=this.c.host.getBoundingClientRect();this.ndc.set((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1);this.ray.setFromCamera(this.ndc,this.c.camera);const h=this.hits(this.ray)[0];return h?{...h,region:this.region(h),anchor:new SurfaceAnchor(h)}:null;}
 pointOnPlane(x,y,z){const r=this.c.host.getBoundingClientRect();this.ndc.set((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1);this.ray.setFromCamera(this.ndc,this.c.camera);return this.ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0,0,1),-z),new THREE.Vector3());}
 segment(from,to){const delta=to.clone().sub(from),distance=delta.length();if(distance<1e-8)return null;const ray=new THREE.Raycaster(from,delta.normalize(),0,distance+.10);const h=this.hits(ray)[0];return h?{...h,region:this.region(h),anchor:new SurfaceAnchor(h)}:null;}
 mouthNear(x,y){if(this.c.studioModel){const center=studioLandmark(this.c.model,'mouth'),p=this.pointOnPlane(x,y,center.z);return !!p&&Math.abs(p.x-center.x)<.25&&Math.abs(p.y-center.y)<.20;}const mouth=this.c.model.getObjectByName('Mouth');if(!mouth)return false;const box=new THREE.Box3().setFromObject(mouth);const center=box.getCenter(new THREE.Vector3());const p=this.pointOnPlane(x,y,center.z);return !!p&&box.expandByScalar(.13).containsPoint(p);}
}
