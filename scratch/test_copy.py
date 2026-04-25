import asyncio, sys
sys.path.append('d:/hermes-agent/scripts')
from perplexity_search import PerplexityCDP

async def test_copy():
    c = PerplexityCDP()
    await c.connect()
    js = """
    (async () => {
        // Find the last answer's copy button
        // Perplexity has multiple copy buttons if there's history. We want the last one.
        let copyBtns = document.querySelectorAll('button[aria-label="Copy"]');
        if(copyBtns.length === 0) return 'Copy button not found';
        
        let copyBtn = copyBtns[copyBtns.length - 1];
        
        let captured = null;
        const originalWrite = navigator.clipboard.writeText;
        navigator.clipboard.writeText = async (text) => { captured = text; };
        
        copyBtn.click();
        await new Promise(r => setTimeout(r, 500));
        
        navigator.clipboard.writeText = originalWrite;
        return captured;
    })()
    """
    md = await c.execute_js(js)
    with open('d:/hermes-agent/scratch/copy_test.md', 'w', encoding='utf-8') as f:
        f.write(str(md))
    await c.ws.close()
    print("Done")

asyncio.run(test_copy())
