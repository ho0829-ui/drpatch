// 주소 두 갈래 (spec v1.25 배포: 화면은 GitHub Pages, API는 이 Mac을 Tailscale Funnel로)
// - asset(): 화면과 같이 나가는 정적 파일(모델·예시·브랜드). Pages는 /sudo-patch/ 아래라 BASE_URL을 붙인다.
// - apiUrl(): 백엔드 API. VITE_API_BASE가 비어 있으면 같은 주소(로컬·Funnel 단독)로 부른다.
const BASE = import.meta.env.BASE_URL || '/';
export const API_BASE = String(import.meta.env.VITE_API_BASE || '').replace(/\/+$/, '');

export const asset = (path) => BASE + String(path).replace(/^\/+/, '');
export const apiUrl = (path) => API_BASE + path;
