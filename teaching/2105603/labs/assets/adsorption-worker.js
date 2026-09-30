import {analyze} from './adsorption.js';self.onmessage=({data})=>{try{self.postMessage({result:analyze(data.dataset,data.window)});}catch(error){self.postMessage({error:error.message});}};
