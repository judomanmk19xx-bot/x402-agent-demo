import { x402Call, X402PaymentRequired } from '../client.js';
function fmtSearch(d) {
    const items = d.results || d.items || [];
    if (!items.length)
        return 'No results.';
    return items
        .slice(0, 10)
        .map((it) => `- ${String(it.title || it.headline || 'untitled').slice(0, 140)}`)
        .join('\n');
}
/** Live web search — free daily trial, then $0.01/call USDC on Base. */
export const webSearchAction = {
    name: 'MEKONG_WEB_SEARCH',
    similes: ['WEB_SEARCH', 'SEARCH_WEB', 'MEKONG_SEARCH'],
    description: 'Search the live web and get deduped, relevance-scored results via the Mekong x402 fleet. ' +
        'No API key needed — free daily trial, then $0.01 per call in USDC on Base. ' +
        'Use when the user asks for current information, news, or anything beyond training data.',
    validate: async () => true,
    handler: async (runtime, message, state, options, callback) => {
        try {
            const text = (message.content.text || '').trim();
            // naive param extraction: "search <query>" or full text as query
            const query = text.replace(/^(search|web search|look up)\s+/i, '').trim() || text;
            const num = 5;
            const data = await x402Call('POST', '/websearch/', { jsonBody: { query, num } });
            const out = fmtSearch(data);
            if (callback)
                await callback({ text: out });
            return { text: out, success: true };
        }
        catch (e) {
            const msg = e instanceof X402PaymentRequired
                ? `Search trial exhausted. ${e.message}`
                : `Search failed: ${e.message}`;
            if (callback)
                await callback({ text: msg, error: true });
            return { text: msg, success: false, error: e };
        }
    },
    examples: [
        [
            { user: 'user', content: { text: 'Search for Ethereum ETF inflows this week' } },
            {
                user: 'assistant',
                content: { text: 'I will search the live web for that.', action: 'MEKONG_WEB_SEARCH' },
            },
        ],
    ],
};
