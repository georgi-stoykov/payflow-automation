// K6 starter: load-test the quote -> payment flow.
// Run:  k6 run k6/quote_payment_load.js
//       SMOKE=1 k6 run k6/quote_payment_load.js   (short CI-friendly profile)
// Docs: https://grafana.com/docs/k6/latest/

import http from 'k6/http';
import { check, sleep } from 'k6';

// SMOKE profile: a ~20s low-VU run with relaxed latency thresholds, meant for
// CI gates on shared runners where full load numbers would be noisy.
const SMOKE = !!__ENV.SMOKE;

export const options = SMOKE ? {
  stages: [
    { duration: '20s', target: 3 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
    checks: ['rate>0.95'],
  },
} : {
  stages: [
    { duration: '15s', target: 10 },  // ramp up to 10 virtual users
    { duration: '30s', target: 10 },  // hold
    { duration: '10s', target: 0 },   // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<300'],      // 95% of requests under 300ms
    http_req_failed: ['rate<0.01'],        // <1% errors
    checks: ['rate>0.99'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const HEADERS = { 'Content-Type': 'application/json' };

export default function () {
  // 1. Get a quote
  const quoteRes = http.post(`${BASE}/api/quotes`, JSON.stringify({
    sell_currency: 'EUR',
    buy_currency: 'USDC',
    amount: Math.round(Math.random() * 99900 + 100) / 100, // 1.00 - 1000.00
  }), { headers: HEADERS });

  check(quoteRes, {
    'quote created (201)': (r) => r.status === 201,
    'quote has amount_out': (r) => r.json('amount_out') !== undefined,
  });

  // 2. Create a payment from the quote
  const payRes = http.post(`${BASE}/api/payments`, JSON.stringify({
    quote_id: quoteRes.json('id'),
    customer_id: 'cus_001',
    idempotency_key: `${__VU}-${__ITER}`, // unique per VU+iteration
  }), { headers: HEADERS });

  check(payRes, {
    'payment created (201)': (r) => r.status === 201,
    'payment pending': (r) => r.json('status') === 'pending',
  });

  // 3. Poll it once
  const getRes = http.get(`${BASE}/api/payments/${payRes.json('id')}`);
  check(getRes, { 'payment retrievable (200)': (r) => r.status === 200 });

  sleep(1);
}
