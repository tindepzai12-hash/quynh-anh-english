import * as THREE from 'three';

// Furniture lives in world coordinates: no accessory bone can stretch the bed.
export function createJustinBed(){
 const bed=new THREE.Group();bed.name='JustinBed';bed.visible=false;
 const materials={wood:new THREE.MeshStandardMaterial({color:'#9ac9d5',roughness:.8}),mattress:new THREE.MeshStandardMaterial({color:'#fff4da',roughness:.96}),pillow:new THREE.MeshStandardMaterial({color:'#fffdf5',roughness:.98}),trim:new THREE.MeshStandardMaterial({color:'#4f96af',roughness:.8})};
 function rounded(name,width,height,depth,radius,material){
  const s=new THREE.Shape(),w=width/2,d=depth/2,r=Math.min(radius,w,d);s.moveTo(-w+r,-d);s.lineTo(w-r,-d);s.quadraticCurveTo(w,-d,w,-d+r);s.lineTo(w,d-r);s.quadraticCurveTo(w,d,w-r,d);s.lineTo(-w+r,d);s.quadraticCurveTo(-w,d,-w,d-r);s.lineTo(-w,-d+r);s.quadraticCurveTo(-w,-d,-w+r,-d);
  const g=new THREE.ExtrudeGeometry(s,{depth:height,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.025,bevelThickness:.025,curveSegments:8});g.rotateX(-Math.PI/2);g.translate(0,-height/2,0);const o=new THREE.Mesh(g,material);o.name=name;o.castShadow=true;o.receiveShadow=true;bed.add(o);return o;
 }
 const frame=rounded('Bed_Frame',1,.18,1.8,.15,materials.wood),mattress=rounded('Bed_Mattress',1,.22,1.65,.18,materials.mattress),pillow=rounded('Bed_Pillow',.85,.18,1.2,.22,materials.pillow);
 const headboard=rounded('Bed_Headboard',.14,.85,1.85,.05,materials.trim);
 const legs=[];for(let i=0;i<4;i++)legs.push(rounded('Bed_Leg_'+i,.16,.46,.16,.05,materials.wood));
 bed.userData.layout=({width,centerX,centerZ,headX,pillowTop})=>{
  const top=.85;frame.scale.x=width;frame.position.set(centerX,top-.28,centerZ);mattress.scale.x=width-.08;mattress.position.set(centerX,top-.11,centerZ);
  pillow.position.set(headX,Math.max(top+.09,pillowTop-.09),centerZ);headboard.position.set(centerX+width/2,top+.08,centerZ);
  legs.forEach((o,i)=>o.position.set(centerX+(i%2?1:-1)*(width/2-.18),.23,centerZ+(i<2?-.63:.63)));
  bed.visible=true;bed.userData.contactHeight=top;
 };
 bed.userData.dispose=()=>{bed.traverse(o=>{if(o.isMesh)o.geometry.dispose()});Object.values(materials).forEach(m=>m.dispose());};
 return bed;
}

export function settleOnBed(model,bed){
 model.updateMatrixWorld(true);
 const body=new THREE.Box3(),head=new THREE.Box3();model.traverse(o=>{
  if(!o.isSkinnedMesh||!o.visible)return;o.skeleton.update();
  if(/^Retopology_(Body|Foot|Leg)|^Relaxed_/.test(o.name))body.expandByObject(o,true);
  if(o.name==='Retopology_Head')head.expandByObject(o,true);
 });
 if(body.isEmpty()||head.isEmpty())return false;
 // Support the torso on the mattress and the head on a separate pillow.
 const delta=.85-body.min.y;
 const offsetX=-body.clone().union(head).getCenter(new THREE.Vector3()).x;
 const offset=new THREE.Vector3(offsetX,delta,0);
 model.position.add(offset);body.translate(offset);head.translate(offset);
 const bounds=body.clone().union(head),center=bounds.getCenter(new THREE.Vector3());
 bed.userData.layout({width:bounds.max.x-bounds.min.x+.55,centerX:center.x,centerZ:center.z,headX:head.getCenter(new THREE.Vector3()).x,pillowTop:head.min.y});
 return true;
}
