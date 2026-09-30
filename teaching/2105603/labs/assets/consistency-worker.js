import {modelingTest} from './consistency.js';
self.onmessage=({data})=>{try{self.postMessage({result:modelingTest(data.set,data.properties)});}catch(e){self.postMessage({error:e.message});}};
