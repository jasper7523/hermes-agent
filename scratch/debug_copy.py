import asyncio, sys
sys.path.append('d:/hermes-agent/scripts')
from perplexity_search import PerplexityCDP

async def debug_copy():
    c = PerplexityCDP()
    await c.connect()
    
    js_check = '''
    (() => {
        let copyBtns = document.querySelectorAll('button[aria-label="Copy"], button[aria-label="複製"], button[aria-label="复制"]');
        return copyBtns.length;
    })()
    '''
    count = await c.execute_js(js_check)
    print('Found buttons:', count)
    
    if count > 0:
        js_copy = '''
        (async () => {
            let copyBtns = document.querySelectorAll('button[aria-label="Copy"], button[aria-label="複製"], button[aria-label="复制"]');
            let copyBtn = copyBtns[copyBtns.length - 1];
            
            let captured = 'default';
            const originalWrite = navigator.clipboard.writeText;
            navigator.clipboard.writeText = async (text) => { captured = text; };
            
            try {
                copyBtn.click();
            } catch(e) {
                return 'Error clicking: ' + e.toString();
            }
            
            for(let i=0; i<30; i++){
                if(captured !== 'default') break;
                await new Promise(r => setTimeout(r, 100));
            }
            
            navigator.clipboard.writeText = originalWrite;
            return captured;
        })()
        '''
        res = await c.execute_js(js_copy)
        if isinstance(res, str):
            print('Result length:', len(res))
            print(res[:200])
        else:
            print("Unknown result:", res)
    await c.ws.close()

asyncio.run(debug_copy())
