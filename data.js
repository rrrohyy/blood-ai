/**
 * blood.ai | DataStore
 * =====================
 * 데이터 접근 계층 (Data Access Layer)
 *
 * 현재 구현: localStorage (브라우저 PoC)
 * 목표 구현: FastAPI 백엔드 REST API 호출
 *
 * 각 메서드 상단에 목표 API 엔드포인트와 DB 매핑을 주석으로 명시.
 * 백엔드 전환 시 이 파일의 메서드 본문만 fetch() 호출로 교체하면
 * index.html(UI 레이어)은 수정 없이 동작한다.
 *
 * 관련 파일:
 *   schema.sql      — 목표 DB 스키마 (PostgreSQL / SQLite)
 *   recommend.py    — 목표 추천 엔진 (Python, FastAPI)
 *   safety_filter.py — 목표 안전 필터 (Python)
 *   seed_data.sql   — 목표 시드 데이터
 */

const DataStore = {

  // ════════════════════════════════════════════════════════
  //  복약 일지 (Diary)
  //  목표 API  : GET    /api/diary          → 목록 조회
  //              POST   /api/diary          → 항목 추가
  //              DELETE /api/diary/{id}     → 항목 삭제
  //  목표 DB   : blood_ai_diary 테이블
  //              (user_id, name, start, dose, added, was_taken, was_stopped)
  // ════════════════════════════════════════════════════════

  getDiary() {
    // 목표: const res = await fetch('/api/diary'); return res.json();
    return JSON.parse(localStorage.getItem('blood_ai_diary') || '[]');
  },

  saveDiary(data) {
    // 목표: 각 항목별 POST/PATCH 호출로 대체 (단순 전체 저장은 사용하지 않음)
    localStorage.setItem('blood_ai_diary', JSON.stringify(data));
  },

  addDiaryEntry(name, start, dose) {
    // 목표: const res = await fetch('/api/diary', { method:'POST', body: JSON.stringify({name,start,dose}) });
    const diary = this.getDiary();
    diary.push({ id: Date.now(), name, start, dose, added: new Date().toISOString() });
    this.saveDiary(diary);
    return diary;
  },

  deleteDiaryEntry(id) {
    // 목표: await fetch(`/api/diary/${id}`, { method:'DELETE' });
    const diary = this.getDiary().filter(d => d.id !== id);
    this.saveDiary(diary);
    return diary;
  },

  // ════════════════════════════════════════════════════════
  //  구내식당 메뉴 (B측 Menu Management)
  //  목표 API  : GET    /api/b2b/menus/{date}       → 날짜별 코스 조회
  //              POST   /api/b2b/menus              → 코스 등록
  //              DELETE /api/b2b/menus/{date}       → 날짜 메뉴 삭제
  //              DELETE /api/b2b/menus              → 전체 삭제
  //  목표 DB   : menu_master 테이블
  //              (company_id, menu_date, course_name, items_text, is_salad_bar)
  // ════════════════════════════════════════════════════════

  getMenuData() {
    // 목표: const res = await fetch('/api/b2b/menus'); return res.json();
    try { return JSON.parse(localStorage.getItem('blood_ai_menu') || '{}'); } catch { return {}; }
  },

  saveMenuData(data) {
    // 목표: 직접 호출 없이 saveMenuForDate / deleteMenuDate 단위로 대체
    localStorage.setItem('blood_ai_menu', JSON.stringify(data));
  },

  getMenuByDate(dateStr) {
    // 목표: const res = await fetch(`/api/b2b/menus/${dateStr}`); return res.json();
    return this.getMenuData()[dateStr] || [];
  },

  saveMenuForDate(dateStr, courses) {
    // 목표: await fetch('/api/b2b/menus', { method:'POST',
    //         body: JSON.stringify({ menu_date: dateStr, courses }) });
    const data = this.getMenuData();
    data[dateStr] = courses;
    this.saveMenuData(data);
  },

  deleteMenuDate(dateStr) {
    // 목표: await fetch(`/api/b2b/menus/${dateStr}`, { method:'DELETE' });
    const data = this.getMenuData();
    delete data[dateStr];
    this.saveMenuData(data);
  },

  clearAllMenus() {
    // 목표: await fetch('/api/b2b/menus', { method:'DELETE' });
    localStorage.removeItem('blood_ai_menu');
  },

  // ════════════════════════════════════════════════════════
  //  PDF 검진 이력 (Blood Test Records)
  //  목표 API  : GET    /api/blood-tests             → 이력 목록 조회
  //              POST   /api/blood-tests/upload      → PDF 파싱 결과 저장
  //              DELETE /api/blood-tests/{id}        → 이력 삭제
  //  목표 DB   : blood_tests 테이블 + biomarker_results 테이블
  //              (source_type: 'pdf_text' 또는 'pdf_ai_ocr')
  // ════════════════════════════════════════════════════════

  getPdfHistory() {
    // 목표: const res = await fetch('/api/blood-tests'); return res.json();
    return JSON.parse(localStorage.getItem('pdf_history') || '[]');
  },

  savePdfHistory(history) {
    // 목표: 직접 호출 없이 addPdfRecord / deletePdfRecord 단위로 대체
    localStorage.setItem('pdf_history', JSON.stringify(history));
  },

  addPdfRecord(record) {
    // 목표: const res = await fetch('/api/blood-tests/upload', {
    //         method:'POST', body: JSON.stringify(record) });
    const history = this.getPdfHistory();
    history.unshift(record);
    this.savePdfHistory(history);
    return history;
  },

  deletePdfRecord(id) {
    // 목표: await fetch(`/api/blood-tests/${id}`, { method:'DELETE' });
    const history = this.getPdfHistory().filter(r => r.id !== id);
    this.savePdfHistory(history);
    return history;
  },

  // ════════════════════════════════════════════════════════
  //  시드 데이터 초기화
  //  목표: 서버사이드 seed_data.sql (SQLite / PostgreSQL INSERT)
  //        → 클라이언트에서 별도 처리 불필요
  // ════════════════════════════════════════════════════════

  seedMenuIfNeeded(sampleMenu) {
    // 목표: 서버 DB에 seed_data.sql이 이미 적재되어 있으므로 이 함수는 삭제
    if (!localStorage.getItem('blood_ai_menu_v2')) {
      this.saveMenuData(sampleMenu);
      localStorage.setItem('blood_ai_menu_v2', '1');
    }
  },

  // ════════════════════════════════════════════════════════
  //  추천 API (FastAPI 백엔드 연동)
  //  목표 API  : POST /api/recommend
  //  현재      : Render 배포 서버 호출 → 실패 시 null 반환 (클라이언트 룰 폴백)
  // ════════════════════════════════════════════════════════

  API_BASE: 'https://blood-ai.onrender.com',

  async getRecommendations(markers, conditions = [], context = {}) {
    try {
      const res = await fetch(`${this.API_BASE}/api/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ markers, conditions, context, top_k: 5 }),
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async getBiomarkers(userId = 'user_001') {
    // 목표: await fetch(`/api/biomarkers/${userId}`)
    try {
      const res = await fetch(`${this.API_BASE}/api/biomarkers/${userId}`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },
};
