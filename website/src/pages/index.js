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
                    NFC 카드나 PIN 번호만 사용하는 기존 방식은 유출이나 복제에 취약하다. 인증 정보가 노출되면 실제 출입자가 누구인지 확인할 방법이 없다는 보안상 한계가 있다.
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
                    1차 인증(NFC/PIN)과 2차 얼굴 인식을 결합한 2단계 인증(2FA) 체계를 구축했다. 모든 단계가 통과되어야만 문이 열리도록 설계하여 보안성을 대폭 강화했다.
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
                { title: "1. 인증 시도", desc: "NFC 카드 태그 또는 키패드 PIN 입력으로 인증 절차를 시작한다." },
                { title: "2. 자격 증명 확인", desc: "서버 데이터베이스를 통해 등록된 사용자의 정보와 일치하는지 검증한다." },
                { title: "3. 얼굴 인식", desc: "YOLOv8 비전 AI가 카메라에 포착된 인물의 신원을 대조하여 본인 여부를 확인한다." },
                { title: "4. 잠금 해제", desc: "모든 인증을 마친 후 서버의 명령에 따라 안전하게 문을 연다." }
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
                  <h3 className="custom-card-title">다중 보안 체계</h3>
                  <p>두 가지 이상의 서로 다른 인증 수단을 결합하여 단일 요소 인증의 취약점을 보완했다.</p>
                </motion.div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">Fail-Secure 설계</h3>
                  <p>서버의 명시적인 허가 없이는 동작하지 않으며, 오류 시에도 잠금 상태를 유지한다.</p>
                </motion.div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <motion.div
                  className="custom-card"
                  style={{height: '100%'}}
                  whileHover={{ scale: 1.05 }}
                >
                  <h3 className="custom-card-title">투명한 기록 관리</h3>
                  <p>모든 출입 시도와 인증 결과를 데이터베이스에 기록하여 사후 추적성을 확보했다.</p>
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
