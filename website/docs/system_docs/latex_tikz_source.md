# LaTeX & TikZ 기반 고해상도 다이어그램 소스

이 문서는 고품질 논문이나 기술 보고서에 사용할 수 있는 LaTeX 및 TikZ 다이어그램 소스 코드를 제공합니다.

## 1. 시스템 블록 다이어그램 (TikZ)

이 코드는 하드웨어와 소프트웨어 간의 상호작용을 정교하게 시각화합니다.

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
