import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--primary button--lg"
            to="/docs/executive-summary">
            View Technical Report
          </Link>
          <Link
            className="button button--outline button--primary button--lg"
            style={{marginLeft: '1rem'}}
            to="/docs/architecture">
            View System Architecture
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  return (
    <Layout
      title="Home"
      description="Technical Report for 2-Factor Authentication Door Lock System">
      <HomepageHeader />
      <main>
        <section className={styles.section}>
          <div className="container">
            <div className="row">
              <div className="col col--6">
                <div className="custom-card">
                  <h2 className="custom-card-title">The Problem</h2>
                  <p>
                    Single-factor door lock systems relying solely on NFC cards or PIN codes are vulnerable to physical theft and unauthorized sharing. If a credential is compromised, the system has no localized method to verify the physical identity of the entrant.
                  </p>
                </div>
              </div>
              <div className="col col--6">
                <div className="custom-card">
                  <h2 className="custom-card-title">The Solution</h2>
                  <p>
                    This experimental prototype implements a strictly enforced Two-Factor Authentication (2FA) pipeline. It requires a valid primary credential (NFC/PIN) paired with an immediate, localized biometric verification (Face Match) before energizing the lock relay.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.sectionAlt}>
          <div className="container">
            <h2 className="text--center margin-bottom--lg">System Pipeline</h2>
            <div className="row text--center">
              <div className="col col--3">
                <div className="custom-card">
                  <h3>1. Input</h3>
                  <p>User presents NFC card or enters PIN on hardware keypad.</p>
                </div>
              </div>
              <div className="col col--3">
                <div className="custom-card">
                  <h3>2. Primary Auth</h3>
                  <p>Backend validates credential against SQLite database.</p>
                </div>
              </div>
              <div className="col col--3">
                <div className="custom-card">
                  <h3>3. Secondary Auth</h3>
                  <p>YOLOv8 Vision module captures and verifies facial identity.</p>
                </div>
              </div>
              <div className="col col--3">
                <div className="custom-card">
                  <h3>4. Actuation</h3>
                  <p>Backend sends explicit unlock command to Arduino relay.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className="container">
            <h2 className="text--center margin-bottom--lg">Key Features</h2>
            <div className="row">
              <div className="col col--4 margin-bottom--md">
                <div className="custom-card" style={{height: '100%'}}>
                  <h3 className="custom-card-title">Sequential 2FA</h3>
                  <p>Software-enforced verification pipeline preventing single-factor bypass.</p>
                </div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <div className="custom-card" style={{height: '100%'}}>
                  <h3 className="custom-card-title">Fail-Secure Hardware</h3>
                  <p>Arduino controller requires continuous, positive authorization from the backend to engage the relay.</p>
                </div>
              </div>
              <div className="col col--4 margin-bottom--md">
                <div className="custom-card" style={{height: '100%'}}>
                  <h3 className="custom-card-title">Immutable Auditing</h3>
                  <p>All success and failure events are logged to an embedded SQLite database.</p>
                </div>
              </div>
            </div>
            <div className="text--center margin-top--lg">
              <Link className="button button--secondary button--lg" to="/dashboard">
                View Validation Status
              </Link>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
