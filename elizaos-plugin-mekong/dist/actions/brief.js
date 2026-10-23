import { x402Call, X402PaymentRequired } from '../client.js';
function fmtBrief(d) {
    for (const key of ['briefing', 'brief', 'summary', 'text']) {
        if (d[key])
            return String(d[key]).slice(0, 4000);
    }
    return JSON.stringify(d).slice(0, 4000);
}
/** Morning-briefing bundle: news + trends + sentiment in one call. Free trial, then $0.05. */
export const briefAction = {
    name: 'MEKONG_BRIEF',
    similes: ['MORNING_BRIEF', 'GET_BRIEFING', 'MEKONG_BRIEFING'],
    description: 'One-call morning briefing from the Mekong x402 fleet: market news headlines, ' +
        'Google Trends intel and news sentiment score for a topic/region. ' +
        'No API key — free daily trial, then $0.05 per call in USDC on Base. ' +
        'Use when the user wants a briefing, market rundown, or sentiment overview.',
    validate: async () => true,
    handler: async (runtime, message, state, options, callback) => {
        try {
            const text = (message.content.text || '').trim();
            const topicMatch = text.match(/(?:brief(?:ing)?|rundown)\s+(?:on|about|for)\s+(.+)/i);
            const topic = (topicMatch?.[1] || 'AI agents').trim().slice(0, 120);
            const geoMatch = text.match(/\b(US|VN|EU|UK|JP|SG)\b/i);
            const geo = (geoMatch?.[1] || 'US').toUpperCase();
            const data = await x402Call('POST', '/brief/', { jsonBody: { topic, geo } });
            const out = fmtBrief(data);
            if (callback)
                await callback({ text: out });
            return { text: out, success: true };
        }
        catch (e) {
            const msg = e instanceof X402PaymentRequired
                ? `Briefing trial exhausted. ${e.message}`
                : `Briefing failed: ${e.message}`;
            if (callback)
                await callback({ text: msg, error: true });
            return { text: msg, success: false, error: e };
        }
    },
    examples: [
        [
            { user: 'user', content: { text: 'Give me a morning briefing on AI agents' } },
            {
                user: 'assistant',
                content: { text: 'I will fetch your briefing.', action: 'MEKONG_BRIEF' },
            },
        ],
    ],
};
