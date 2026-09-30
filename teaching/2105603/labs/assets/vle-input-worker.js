import {fitVLE} from './vle-input.js';
self.onmessage=({data})=>{try{self.postMessage({result:fitVLE(data.set,data.options)});}catch(error){self.postMessage({error:error.message});}};
