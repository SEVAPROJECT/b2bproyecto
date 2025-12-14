import http from 'k6/http';
import { check, sleep } from 'k6';

// 🔹 ESCENARIO DE CARGA
export const options = {
  stages: [
    { duration: '1m', target: 10 },  // Subir a 10 usuarios en 1 min
    { duration: '3m', target: 10 },  // Mantener 10 usuarios por 3 min
    { duration: '1m', target: 50 },  // Subir a 50 usuarios en 1 min
    { duration: '3m', target: 50 },  // Mantener 50 usuarios por 3 min
    { duration: '1m', target: 0 },   // Bajar a 0
  ],
  thresholds: {
    // p(95) = 95% de las requests deben ser menores a 800 ms
    http_req_duration: ['p(95)<800'],
    // Menos del 1% de errores
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = 'https://frontend-production-ee3b.up.railway.app/#/login'; // 👉 reemplazá por URL

export default function () {
  // 1) Definí qué request representa el “uso típico”
  const res = http.get(`${BASE_URL}/ruta-principal`);

  // 2) Validaciones básicas
  check(res, {
    'status es 200': (r) => r.status === 200,
  });

  // 3) Pequeña pausa para simular usuario real
  sleep(1);
}
