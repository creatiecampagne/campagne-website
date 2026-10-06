/**
 * Campagne — contactformulier (Cloudflare Pages Function)
 * =======================================================
 * Bereikbaar op /api/contact (alleen POST). Draait op de servers van
 * Cloudflare, niet in de browser — de geheime sleutels zijn dus nooit
 * zichtbaar voor bezoekers.
 *
 * Wat er gebeurt bij een inzending:
 *  1. Herkomst: alleen inzendingen vanaf onze eigen site worden aangenomen.
 *  2. Lokveld: het onzichtbare veld "website" moet leeg zijn. Mensen zien het
 *     niet, bots vullen alles in — die krijgen een nep-"gelukt" en verder niets.
 *  3. Controle: naam en geldig e-mailadres verplicht, maximale lengtes.
 *  4. Turnstile: het bewijs uit de browser ("ik ben een mens") wordt hier bij
 *     Cloudflare gecontroleerd. Zonder geldig bewijs geen mail.
 *  5. Pas dan gaat de mail via Resend naar MAIL_NAAR, met het adres van de
 *     afzender als antwoordadres.
 *
 * Er wordt niets opgeslagen: het bericht wordt alleen doorgestuurd (AVG).
 *
 * Instellingen — Cloudflare → Workers & Pages → campagne-website →
 * Settings → Variables and Secrets (voor Production én Preview):
 *   TURNSTILE_SECRET   geheim   Secret key van de Turnstile-widget
 *   RESEND_API_KEY     geheim   API-sleutel van Resend
 *   MAIL_NAAR                   ontvanger, bijv. hello@campagne.nl
 *   MAIL_VAN           optie    afzender. Zolang campagne.nl niet bij Resend is
 *                               geverifieerd: "Campagne website <onboarding@resend.dev>"
 */

const MAX = { naam: 120, email: 200, bericht: 5000 };

export async function onRequestPost({ request, env }) {
  // 1. Herkomst
  const herkomst = request.headers.get('Origin');
  if (herkomst && new URL(herkomst).host !== new URL(request.url).host) {
    return antwoord(403, 'herkomst');
  }

  if (!env.TURNSTILE_SECRET || !env.RESEND_API_KEY || !env.MAIL_NAAR) {
    console.log('Contactformulier: instellingen ontbreken (TURNSTILE_SECRET, RESEND_API_KEY of MAIL_NAAR)');
    return antwoord(500, 'instellingen');
  }

  let data;
  try {
    data = Object.fromEntries(await request.formData());
  } catch {
    return antwoord(400, 'ongeldig');
  }

  // 2. Lokveld
  if (data.website) return antwoord(200, 'ok');

  // 3. Controle
  const naam = enkeleRegel(data.naam).slice(0, MAX.naam + 1);
  const email = enkeleRegel(data.email);
  const bericht = String(data.bericht || '').trim();
  if (!naam || naam.length > MAX.naam) return antwoord(400, 'naam');
  if (email.length > MAX.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return antwoord(400, 'email');
  if (bericht.length > MAX.bericht) return antwoord(400, 'bericht');

  // 4. Turnstile
  const token = data['cf-turnstile-response'];
  if (!token) return antwoord(400, 'turnstile');
  const controle = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: new URLSearchParams({
      secret: env.TURNSTILE_SECRET,
      response: token,
      remoteip: request.headers.get('CF-Connecting-IP') || '',
    }),
  }).then((r) => r.json()).catch(() => ({ success: false }));
  if (!controle.success) return antwoord(403, 'turnstile');

  // 5. Versturen
  const site = new URL(request.url).host;
  const mail = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: env.MAIL_VAN || 'Campagne website <onboarding@resend.dev>',
      to: [env.MAIL_NAAR],
      reply_to: email,
      subject: `Wanna be loved? — bericht van ${naam}`,
      text: `${bericht || '(geen bericht ingevuld)'}\n\n—\n${naam}\n${email}\n\nVerstuurd via het contactformulier op ${site}`,
    }),
  });
  if (!mail.ok) {
    console.log('Contactformulier: versturen mislukt', mail.status, await mail.text());
    return antwoord(502, 'versturen');
  }
  return antwoord(200, 'ok');
}

function enkeleRegel(waarde) {
  return String(waarde || '').replace(/[\r\n]+/g, ' ').trim();
}

function antwoord(status, code) {
  return new Response(JSON.stringify({ ok: status === 200, code }), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}
