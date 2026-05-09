import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: '다중 보안 체계',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        NFC/PIN 1차 인증과 얼굴 인식 2차 인증을 결합하여 보안 수준을 강화했습니다.
      </>
    ),
  },
  {
    title: 'Fail-Secure 설계',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        서버의 명시적 승인 없이는 잠금이 해제되지 않으며, 장애 시에도 안전을 유지합니다.
      </>
    ),
  },
  {
    title: '투명한 기록 관리',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        모든 출입 시도와 인증 결과를 실시간으로 기록하여 철저한 감사 이력을 제공합니다.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
