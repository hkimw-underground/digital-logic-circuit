import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import { motion } from 'framer-motion';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <motion.h1
          className="hero__title"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {siteConfig.title}
        </motion.h1>
        <motion.p
          className="hero__subtitle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {siteConfig.tagline}
        </motion.p>
        <motion.div
          className={styles.buttons}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Link
            className="button button--primary button--lg"
            to="/docs/executive-summary">
            요약 보고서 보기
          </Link>
          <Link
            className="button button--outline button--primary button--lg"
            style={{marginLeft: '1rem'}}
            to="/docs/architecture">
            시스템 아키텍처 보기
          </Link>
        </motion.div>
      </div>
    </header>
  );
}

export default function Home() {
  return (
    <Layout
      title="홈"
      description="지능형 이중 인증 기반 스마트 도어락 기술 보고서">
      <HomepageHeader />
      <main>
        <section className={styles.section}>
          <div className="container">
            <div className="row">
              <div className="col col--6">
                <motion.div
                  className="custom-card"
                  whileHover={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <h2 className="custom-card-title">문제 배경</h2>
                  <p>
                    NFC 카드나 PIN 코드 중심의 단일 인증 방식은 물리적 탈취 및 복제에 취약하며, 권한 도용 시 실제 사용자 여부를 검증하기 어렵다.
                  </p>
                </motion.div>
              </div>
              <div className="col col--6">
                <motion.div
                  className="custom-card"
                  whileHover={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <h2 className="custom-card-title">핵심 솔루션</h2>
                  <p>
                    NFC/PIN 1차 인증과 YOLOv8 기반 실시간 얼굴 인식을 결합한 2단계 인증(2FA)을 구현하여, 물리적 보안과 생체 검증이 공존하는 안정적인 출입 통제 환경을 구축한다.
                  </p>
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.sectionAlt}>
          <div className="container">
            <h2 className="text--center margin-bottom--lg">시스템 파이프라인</h2>
            <div className="row text--center">
              {[
                { title: "1. 접근 요청", desc: "사용자의 PIN 입력 또는 NFC 태그를 통해 인증 프로세스를 시작한다." },
                { title: "2. 자격 검증", desc: "SQLite 데이터베이스 연동을 통해 1차 자격 증명의 유효성을 확인한다." },
                { title: "3. 생체 인식", desc: "YOLOv8 비전 모듈이 실시간으로 얼굴 신원을 분석하여 본인 여부를 식별한다." },
                { title: "4. 잠금 해제", desc: "모든 인증 단계를 통과한 경우에만 Arduino 서보에 OPEN_DOOR 명령을 전송한다." }
              ].map((item, i) => (
                <div className="col col--3" key={i}>
                  <motion.div
                    className="custom-card"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1, duration: 0.5 }}
                    whileHover={{ y: -5 }}
                  >
                    <h3>{item.title}</h3>
                    <p>{item.desc}</p>
                  </motion.div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className="container">
            <h2 className="text--center margin-bottom--lg">주요 기능</h2>
            <div className="row">
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">상호 보완적 2FA</h3>
                  <p>물리 매체와 생체 인식을 순차적으로 결합하여 단일 인증의 보안 허점을 근본적으로 보완한다.</p>
                </motion.div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">Fail-Secure 설계</h3>
                  <p>시스템 장애나 통신 중단 시에도 상시 잠금을 유지하여 하드웨어 차원의 보안을 확보한다.</p>
                </motion.div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">투명한 이력 관리</h3>
                  <p>모든 인증 및 접근 시도를 데이터베이스에 기록하여 누락 없는 사후 감사를 지원한다.</p>
                </motion.div>
              </div>
            </div>
            <div className="text--center margin-top--lg">
              <Link className="button button--secondary button--lg" to="/dashboard">
                검증 상태 보기
              </Link>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
