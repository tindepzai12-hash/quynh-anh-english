import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as THREE from '../public/vendor/three/three.module.js';
import {loadPetModule} from './load-pet-module.mjs';
const {InteractionEffects}=await loadPetModule('InteractionEffects');
const {BodySurface}=await loadPetModule('BodySurface');
const {EmotionEngine}=await loadPetModule('EmotionEngine');
function fixture(){const model=new THREE.Group();const head=new THREE.Mesh(new THREE.BoxGeometry(1,1,1));head.name='Retopology_Head';head.position.y=2;model.add(head);const camera=new THREE.PerspectiveCamera();camera.position.set(0,2,5);const c={scene:new THREE.Scene(),model,camera,host:{dataset:{}},state:{current:'Interacting'},animation:{talking:false,amplitude:0},emotion:new EmotionEngine(),options:{},notify:()=>{}};c.scene.add(model);c.surface=new BodySurface(c);return [c,new InteractionEffects(c)];}
for(const reduced of [false,true])for(const kind of ['pet','poke','ball','feed'])test(`${kind}, reduced motion=${reduced}: impact, cleanup, neutral pose`,()=>{const[c,fx]=fixture();let hits=0;fx.start(kind,undefined,()=>hits++);for(let i=0;i<200;i++){fx.update(.016,reduced);assert.ok(c.model.position.toArray().every(Number.isFinite));}assert.equal(hits,1);assert.equal(fx.active,null);assert.equal(fx.group.children.length,0);assert.ok(c.model.position.length()<1e-10);assert.equal(c.model.rotation.z,0);assert.equal(c.animation.talking,false);fx.dispose();assert.equal(c.scene.children.length,1);});
test('interruption disposes props and restores recoil without a late impact',()=>{const[c,fx]=fixture();let hits=0;fx.start('ball',undefined,()=>hits++);for(let i=0;i<60;i++)fx.update(.016);assert.equal(hits,1);fx.start('feed');fx.update(.2);fx.clear();fx.update(5);assert.equal(hits,1);assert.equal(c.model.position.length(),0);assert.equal(fx.group.children.length,0);});
