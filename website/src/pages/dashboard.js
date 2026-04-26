import React from 'react';
import Layout from '@theme/Layout';

export default function Dashboard() {
  return (
    <Layout title="시스템 모니터링 대시보드" description="2FA 스마트 도어락 실시간 통계">
      <main style={{padding: '2rem', maxWidth: '1200px', margin: '0 auto'}}>
        <h1>시스템 모니터링 대시보드 (Mock)</h1>
        <p>프로젝트의 현재 상태를 실시간으로 시각화합니다.</p>

        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem'}}>
          <div style={{border: '1px solid #ddd', padding: '1rem', borderRadius: '8px'}}>
            <h3>오늘의 출입 통계</h3>
            <div style={{height: '300px', background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
               [ Chart.js / ECharts 렌더링 영역: 출입 시간대별 선형 그래프 ]
            </div>
          </div>

          <div style={{border: '1px solid #ddd', padding: '1rem', borderRadius: '8px'}}>
            <h3>인증 수단별 분포</h3>
            <div style={{height: '300px', background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
               [ Chart.js / ECharts 렌더링 영역: NFC vs PIN 파이 차트 ]
            </div>
          </div>

          <div style={{border: '1px solid #ddd', padding: '1rem', borderRadius: '8px'}}>
            <h3>최근 보안 위협 탐지</h3>
            <div style={{height: '300px', background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
               [ ECharts 렌더링 영역: 요일별 차단 시도 막대 그래프 ]
            </div>
          </div>

          <div style={{border: '1px solid #ddd', padding: '1rem', borderRadius: '8px'}}>
            <h3>AI 모델 인식률 (YOLOv8)</h3>
            <div style={{height: '300px', background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
               [ Chart.js 렌더링 영역: 신뢰도 분포 레이더 차트 ]
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}
