import http from 'k6/http';
import { check, sleep } from 'k6';

// ESCALABILIDAD: 100 → 300 → 500 VUs
export const options = {
  stages: [
    // Calentamiento
    { duration: '2m', target: 100 },
    { duration: '3m', target: 100 },

    // Salto a 300
    { duration: '3m', target: 300 },
    { duration: '5m', target: 300 },

    // Salto a 500
    { duration: '3m', target: 500 },
    { duration: '5m', target: 500 },

    // Bajada
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: [
      'avg<500',
      'p(95)<800',
    ],
    http_req_failed: ['rate<0.01'],
  },
};

const URL_UNDER_TEST = __ENV.URL_UNDER_TEST || 'https://frontend-production-ee3b.up.railway.app/#/marketplace';

export default function () {
  const res = http.get(URL_UNDER_TEST);

  check(res, {
    'status es 200': (r) => r.status === 200,
  });

  sleep(1);
}
