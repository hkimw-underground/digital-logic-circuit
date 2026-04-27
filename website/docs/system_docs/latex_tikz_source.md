---
title: "LaTeX 다이어그램 소스"
sidebar_label: "LaTeX 소스"
---

# LaTeX 다이어그램 소스

LaTeX(라텍)는 학술 논문이나 기술 보고서 작성에 널리 쓰이는 조판(문서 편집) 언어이며,
TikZ(티크즈)는 LaTeX 안에서 고해상도 다이어그램을 그리는 패키지(도구 묶음)입니다.
아래 소스 코드를 Overleaf(온라인 LaTeX 편집기) 또는 로컬 LaTeX 환경에 붙여넣으면
고품질 벡터 이미지를 생성할 수 있습니다.

## 1. 시스템 블록 다이어그램 (TikZ)

하드웨어(Arduino)와 소프트웨어(Python 서버, AI, 데이터베이스) 간의 연결 관계를
정교하게 시각화합니다. 논문 또는 최종 보고서 첨부용으로 사용합니다.

```latex
\documentclass[tikz, border=10pt]{standalone}
\usetikzlibrary{shapes.geometric, arrows, positioning}

\tikzstyle{hw} = [rectangle, rounded corners, minimum width=3cm, minimum height=1cm,text centered, draw=blue!70, fill=blue!10]
\tikzstyle{sw} = [rectangle, rounded corners, minimum width=3cm, minimum height=1cm,text centered, draw=green!70, fill=green!10]
\tikzstyle{db} = [cylinder, draw=orange!70, fill=orange!10, shape border rotate=90, minimum width=2cm, minimum height=1.5cm, text centered]
\tikzstyle{arrow} = [thick,->,>=stealth]

\begin{document}
\begin{tikzpicture}[node distance=2cm]

% Nodes
\node (arduino) [hw] {Arduino (Controller)};
\node (nfc) [hw, left=of arduino] {NFC Reader};
\node (keypad) [hw, below left=0.5cm and 0.2cm of arduino] {Keypad};
\node (relay) [hw, right=of arduino] {Relay / Door};

\node (server) [sw, above=2cm of arduino] {Python Server (FastAPI)};
\node (vision) [sw, right=of server] {Vision AI (YOLOv8)};
\node (database) [db, left=of server] {SQLite Database};

% Arrows
\draw [arrow] (nfc) -- (arduino);
\draw [arrow] (keypad) |- (arduino);
\draw [arrow] (arduino) -- node[anchor=south] {OPEN\_DOOR} (relay);
\draw [arrow] (arduino) -- node[anchor=left] {Serial} (server);
\draw [arrow] (server) -- (vision);
\draw [arrow] (server) -- (database);
\draw [arrow] (vision) -- (database);

\end{tikzpicture}
\end{document}
```

## 2. 인증 시퀀스 다이어그램 (TikZ)

사용자 인증이 진행되는 순서를 시간 축 기준으로 나타냅니다.
각 구성 요소(사용자, 하드웨어, 서버, AI) 간의 메시지 흐름을 한눈에 파악할 수 있습니다.

```latex
\documentclass[tikz, border=10pt]{standalone}
\usetikzlibrary{arrows.meta}

\begin{document}
\begin{tikzpicture}[>=Stealth, font=\sffamily]
    % Lifelines
    \draw[thick] (0,0) -- (0,-8) node[below] {User};
    \draw[thick] (3,0) -- (3,-8) node[below] {Hardware};
    \draw[thick] (6,0) -- (6,-8) node[below] {Server};
    \draw[thick] (9,0) -- (9,-8) node[below] {Vision AI};

    % Interactions
    \draw[->] (0,-1) -- node[above] {Tag NFC/PIN} (3,-1);
    \draw[->] (3,-2) -- node[above] {Wakeup Event} (6,-2);
    \draw[->] (6,-3) -- node[above, sloped] {DB Match OK} (6,-3.5);
    \draw[->] (6,-4) -- node[above] {Request Face} (9,-4);
    \draw[->] (9,-5) -- node[above] {Liveness Check} (0,-5);
    \draw[->] (9,-6) -- node[above] {Match Success} (6,-6);
    \draw[->] (6,-7) -- node[above] {OPEN\_DOOR} (3,-7);
\end{tikzpicture}
\end{document}
```
