import * as THREE from 'three';
// The mask is a custom GLB attribute, not COLOR_0: it must never tint the skin.
export async function installBlink(model) {
 const closed=await new THREE.TextureLoader().loadAsync('/assets/justin-mini/studio-v39/closed-eyes.png');
 closed.flipY=false;closed.colorSpace=THREE.SRGBColorSpace;
 const amount={value:0};let installed=0;
 model.traverse(o=>{
  if(!o.isMesh||!o.material.name.includes('Original-PBR'))return;
  if(!o.geometry.attributes._justin_face_mask)throw new Error('GLB thiếu dữ liệu mí mắt');
  const material=o.material;material.vertexColors=false;
  material.customProgramCacheKey=()=> 'JustinMiniEyelidWipe-v1';
  material.onBeforeCompile=shader=>{
   shader.uniforms.justinBlink=amount;shader.uniforms.justinClosed={value:closed};
   shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute vec3 _justin_face_mask; varying vec2 justinFaceMask;').replace('#include <begin_vertex>','#include <begin_vertex>\njustinFaceMask=_justin_face_mask.rg;');
   shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nuniform float justinBlink; uniform sampler2D justinClosed; varying vec2 justinFaceMask;').replace('#include <map_fragment>',`#include <map_fragment>
    float jb=clamp(justinBlink,0.0,1.0);
    if(jb>.001){
     vec3 closedColour=texture2D(justinClosed,vMapUv).rgb;
     float wipe=clamp((justinFaceMask.r-(1.0-jb))/.04+.5,0.0,1.0)*step(.25,justinFaceMask.g);
     wipe=max(wipe,smoothstep(.9,1.0,jb))*step(.25,justinFaceMask.g);
     vec3 lid=mix(vec3(.001518,.266356,1.0),closedColour,smoothstep(.85,1.0,jb));
     float edge=(1.0-smoothstep(.008,.018,abs(justinFaceMask.r-(1.0-jb))))*step(.25,justinFaceMask.g)*step(.005,jb)*(1.0-smoothstep(.82,.98,jb));
     lid=mix(lid,vec3(.005,.028,.095),edge);
     diffuseColor.rgb=mix(diffuseColor.rgb,lid,wipe);
    }`);
  };
  material.needsUpdate=true;installed++;
 });
 if(!installed)throw new Error('Không tìm thấy material khuôn mặt');
 return {amount,installed,dispose:()=>closed.dispose()};
}
