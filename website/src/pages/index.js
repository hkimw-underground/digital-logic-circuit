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
      description="2단계 인증 도어락 시스템 기술 보고서">
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
                  <h2 className="custom-card-title">문제</h2>
                  <p>
                    NFC 카드나 PIN 코드에 전적으로 의존하는 단일 요소 인증 시스템은 물리적 도난이나 비밀번호 공유에 취약하다. 자격 증명이 노출될 경우, 시스템은 출입자의 실제 신원을 확인할 로컬 수단이 없다.
                  </p>
                </motion.div>
              </div>
              <div className="col col--6">
                <motion.div
                  className="custom-card"
                  whileHover={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <h2 className="custom-card-title">해결책</h2>
                  <p>
                    이 실험적 프로토타입은 엄격하게 시행되는 2단계 인증(2FA) 파이프라인을 구현한다. 잠금 릴레이를 해제하기 전에 유효한 1차 자격 증명(NFC/PIN)과 즉각적인 로컬 생체 검증을 모두 요구한다.
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
                { title: "1. 입력", desc: "사용자가 하드웨어 키패드에 PIN을 입력하거나 NFC 카드를 태그한다." },
                { title: "2. 1차 인증", desc: "Backend가 SQLite 데이터베이스를 통해 자격 증명을 검증한다." },
                { title: "3. 2차 인증", desc: "YOLOv8 Vision 모듈이 얼굴 신원을 캡처하고 확인한다." },
                { title: "4. 작동", desc: "Backend가 Arduino 릴레이에 명시적인 잠금 해제 명령을 보낸다." }
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
                  <h3 className="custom-card-title">순차적 2FA</h3>
                  <p>단일 요소 우회를 방지하는 소프트웨어 기반 검증 파이프라인.</p>
                </motion.div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">Fail-Secure 하드웨어</h3>
                  <p>Arduino 컨트롤러는 릴레이를 작동시키기 위해 Backend로부터 지속적이고 긍정적인 권한 부여를 요구한다.</p>
                </motion.div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">변경 불가능한 감사</h3>
                  <p>모든 성공 및 실패 이벤트가 임베디드 SQLite 데이터베이스에 로깅된다.</p>
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
