import { ArrowRight, Check, ExternalLink, X } from 'lucide-react'
import { useEffect, useRef, useState, type CSSProperties, type MouseEvent, type PointerEvent, type WheelEvent } from 'react'
import { Link } from 'react-router-dom'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  governanceCards,
  governanceLayerLabels,
  governanceLoopSteps,
  heroTitle,
  scannerHits,
  scannerMissingControls,
  fileStatusCards,
  proofPoints,
  safetyBoundaries,
  sampleFamilies,
  workflowNodeLabels,
  workflowPhases,
  workflowStepPhaseIndexes,
  workflowSteps,
  workflowThreadPath,
  type GovernanceCardConfig,
} from './homePageContent'
import { prefersReducedMotion, useDotGridCanvas } from './homePageMotion'
import { PublicAnalysisTrial } from './PublicAnalysisTrial'
import { TrueFocus } from './TrueFocus'
import './HomePage.css'
import './HomePage.sections.css'
import './HomePage.responsive.css'

gsap.registerPlugin(ScrollTrigger)

export function HomePage() {
  const rootRef = useRef<HTMLDivElement>(null)
  const dotGridCanvasRef = useRef<HTMLCanvasElement>(null)
  const fileStatusDragStartXRef = useRef(0)
  const fileStatusDragStartIndexRef = useRef(0)
  const fileStatusDidDragRef = useRef(false)
  const fileStatusWheelTimerRef = useRef<number | null>(null)
  const [activeWorkflowNodeIndex, setActiveWorkflowNodeIndex] = useState<number | null>(null)
  const [visibleHeroTitleLength, setVisibleHeroTitleLength] = useState(() => (prefersReducedMotion() ? heroTitle.length : 0))
  const [heroTitleOpacity, setHeroTitleOpacity] = useState(() => (prefersReducedMotion() ? 1 : 0))
  const [isHeroTitleTyping, setIsHeroTitleTyping] = useState(() => !prefersReducedMotion())
  const [isWorkflowDetailOpen, setIsWorkflowDetailOpen] = useState(false)
  const [activeGovernanceIndex, setActiveGovernanceIndex] = useState(0)
  const [isGovernanceFolderOpen, setIsGovernanceFolderOpen] = useState(false)
  const [activeFileStatusIndex, setActiveFileStatusIndex] = useState(0)
  const [fileStatusDragOffset, setFileStatusDragOffset] = useState(0)
  const [isFileStatusDragging, setIsFileStatusDragging] = useState(false)
  const [isFileStatusHovered, setIsFileStatusHovered] = useState(false)
  const visibleHeroTitle = heroTitle.slice(0, visibleHeroTitleLength)
  const visibleWorkflowNodeIndex = activeWorkflowNodeIndex ?? 0
  const visibleWorkflowPhase = workflowPhases[visibleWorkflowNodeIndex]
  const activeGovernanceCard = governanceCards[activeGovernanceIndex] ?? governanceCards[0]
  const activeFileStatus = fileStatusCards[activeFileStatusIndex] ?? fileStatusCards[0]

  useDotGridCanvas(dotGridCanvasRef)

  function handleSectionLink(event: MouseEvent<HTMLAnchorElement>, sectionId: string) {
    const section = document.getElementById(sectionId)

    if (!section) {
      return
    }

    event.preventDefault()
    window.history.replaceState(null, '', `#${sectionId}`)
    section.scrollIntoView({ behavior: 'auto', block: 'start' })
    window.setTimeout(() => section.focus({ preventScroll: true }), 0)
  }

  function handleHeroCardPointerMove(event: PointerEvent<HTMLDivElement>) {
    const bounds = event.currentTarget.getBoundingClientRect()
    const x = (event.clientX - bounds.left) / bounds.width - 0.5
    const y = (event.clientY - bounds.top) / bounds.height - 0.5
    const maxTilt = 5

    event.currentTarget.style.setProperty('--tilt-x', `${(-y * maxTilt).toFixed(2)}deg`)
    event.currentTarget.style.setProperty('--tilt-y', `${(x * maxTilt).toFixed(2)}deg`)
  }

  function handleHeroCardPointerLeave(event: PointerEvent<HTMLDivElement>) {
    event.currentTarget.style.setProperty('--tilt-x', '0deg')
    event.currentTarget.style.setProperty('--tilt-y', '0deg')
  }

  function selectPreviousWorkflowPhase() {
    setActiveWorkflowNodeIndex((current) => Math.max((current ?? 0) - 1, 0))
  }

  function selectNextWorkflowPhase() {
    setActiveWorkflowNodeIndex((current) => Math.min((current ?? 0) + 1, workflowNodeLabels.length - 1))
  }

  function openWorkflowPhase(index: number) {
    setActiveWorkflowNodeIndex(index)
    setIsWorkflowDetailOpen(true)
  }

  function openWorkflowStep(stepIndex: number) {
    openWorkflowPhase(workflowStepPhaseIndexes[stepIndex] ?? 0)
  }

  function resetWorkflowPhase() {
    setActiveWorkflowNodeIndex(null)
    setIsWorkflowDetailOpen(false)
  }

  function selectGovernanceCard(index: number) {
    setIsGovernanceFolderOpen(true)
    setActiveGovernanceIndex(index)
  }

  function selectFileStatus(index: number) {
    const total = fileStatusCards.length
    const nextIndex = ((index % total) + total) % total

    setActiveFileStatusIndex(nextIndex)
    setFileStatusDragOffset(0)
  }

  function handleFileStatusPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (event.pointerType === 'mouse' && event.button !== 0) return

    fileStatusDragStartXRef.current = event.clientX
    fileStatusDragStartIndexRef.current = activeFileStatusIndex
    fileStatusDidDragRef.current = false
    setIsFileStatusDragging(true)
    setFileStatusDragOffset(0)
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function handleFileStatusPointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!isFileStatusDragging) return

    const nextOffset = event.clientX - fileStatusDragStartXRef.current
    if (Math.abs(nextOffset) > 8) {
      fileStatusDidDragRef.current = true
    }

    setFileStatusDragOffset(nextOffset)
  }

  function handleFileStatusPointerEnd(event: PointerEvent<HTMLDivElement>) {
    if (!isFileStatusDragging) return

    const cardStep = 180
    const indexShift = Math.round(-fileStatusDragOffset / cardStep)
    const nextIndex = fileStatusDragStartIndexRef.current + indexShift

    setIsFileStatusDragging(false)
    selectFileStatus(nextIndex)
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  function handleFileStatusWheel(event: WheelEvent<HTMLDivElement>) {
    const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY

    if (Math.abs(delta) < 24 || fileStatusWheelTimerRef.current !== null) return

    event.preventDefault()
    selectFileStatus(activeFileStatusIndex + (delta > 0 ? 1 : -1))
    fileStatusWheelTimerRef.current = window.setTimeout(() => {
      fileStatusWheelTimerRef.current = null
    }, 420)
  }

  function getFileStatusPosition(index: number) {
    const total = fileStatusCards.length
    let position = index - activeFileStatusIndex

    if (position > total / 2) position -= total
    if (position < -total / 2) position += total

    return position + fileStatusDragOffset / 180
  }

  function renderGovernanceCardContent(card: GovernanceCardConfig, isActive: boolean) {
    if (!isActive) {
      return <p className="landing-governance-card-summary">{card.summary}</p>
    }

    switch (card.type) {
      case 'toggles':
        return (
          <div className="landing-governance-toggle-list">
            {[
              ['Require review justification', true],
              ['Mask evidence by default', true],
              ['Delete external files automatically', false],
            ].map(([label, isOn]) => (
              <div className="landing-governance-toggle-row" key={String(label)}>
                <span>{label}</span>
                <i className={`landing-governance-toggle${isOn ? ' landing-governance-toggle-on' : ''}`} aria-hidden="true" />
              </div>
            ))}
          </div>
        )
      case 'codeRule':
        return (
          <div className="landing-governance-code">
            <div>IF risk == <mark>high</mark></div>
            <div>AND category == <mark>special_category</mark></div>
            <div>THEN route_to = <mark>DPO escalation</mark></div>
          </div>
        )
      case 'permissionBoundary':
        return (
          <div className="landing-governance-boundary">
            <div>
              <strong>Scanner can</strong>
              {['Detect GDPR-relevant signals', 'Suggest review context'].map((item) => (
                <span key={item}><Check aria-hidden="true" size={15} />{item}</span>
              ))}
            </div>
            <div>
              <strong>Scanner cannot</strong>
              {['Delete external files', 'Reveal masked values'].map((item) => (
                <span className="landing-governance-denied" key={item}><X aria-hidden="true" size={15} />{item}</span>
              ))}
            </div>
          </div>
        )
      case 'ownerRouting':
        return (
          <div className="landing-governance-routing">
            {[
              ['Assigned Source', 'Direct Owner'],
              ['Workspace Source', 'Source Owner'],
              ['Unknown Owner', 'Master of Data'],
              ['High Risk + Unknown Owner', 'DPO Escalation'],
            ].map(([source, owner]) => (
              <div key={source}>
                <span>{source}</span>
                <b>to</b>
                <strong>{owner}</strong>
              </div>
            ))}
          </div>
        )
      case 'reviewerGuidance':
        return (
          <div className="landing-governance-guidance">
            <span>Detected</span>
            <strong>Health Data + Personal Identifier</strong>
            <span>Suggested Action</span>
            <b>Escalate before cleanup</b>
            <em>Justification before decision</em>
          </div>
        )
      case 'auditRequirement':
        return (
          <div className="landing-governance-audit">
            <span>Audit-ready</span>
            {['Actor', 'Evidence', 'Decision', 'Justification', 'Timestamp'].map((item) => (
              <div key={item}><Check aria-hidden="true" size={15} />{item}</div>
            ))}
          </div>
        )
      default:
        return null
    }
  }

  useEffect(() => {
    if (prefersReducedMotion() || isFileStatusDragging || isFileStatusHovered) {
      return undefined
    }

    const interval = window.setInterval(() => {
      setActiveFileStatusIndex((index) => (index + 1) % fileStatusCards.length)
      setFileStatusDragOffset(0)
    }, 3200)

    return () => window.clearInterval(interval)
  }, [isFileStatusDragging, isFileStatusHovered])

  useEffect(() => {
    return () => {
      if (fileStatusWheelTimerRef.current !== null) {
        window.clearTimeout(fileStatusWheelTimerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    const root = rootRef.current
    if (!root) {
      return
    }

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const ctx = gsap.context(() => {
      if (prefersReducedMotion) {
        return
      }

      gsap.from('.landing-nav-shell', {
        autoAlpha: 0,
        duration: 0.7,
        ease: 'power3.out',
        y: -16,
      })

      gsap.from('.landing-hero-copy > :not(.landing-hero-title)', {
        autoAlpha: 0,
        duration: 0.85,
        ease: 'power3.out',
        stagger: 0.08,
        y: 28,
      })

      gsap.to('.landing-parallax-slow', {
        scrollTrigger: {
          end: 'bottom top',
          scrub: 1.1,
          start: 'top top',
          trigger: '.landing-hero',
        },
        y: -90,
      })

      gsap.to('.landing-parallax-medium', {
        rotation: -2,
        scrollTrigger: {
          end: 'bottom top',
          scrub: 0.9,
          start: 'top top',
          trigger: '.landing-hero',
        },
        x: 28,
        y: -145,
      })

      gsap.to('.landing-parallax-fast', {
        rotation: 3,
        scrollTrigger: {
          end: 'bottom top',
          scrub: 0.75,
          start: 'top top',
          trigger: '.landing-hero',
        },
        x: -34,
        y: -205,
      })

      gsap.to('.landing-workflow-depth-grid', {
        scrollTrigger: {
          end: 'bottom top',
          scrub: 1.15,
          start: 'top bottom',
          trigger: '.landing-workflow',
        },
        y: -96,
      })

      gsap.utils.toArray<HTMLElement>('.landing-reveal').forEach((element) => {
        gsap.from(element, {
          autoAlpha: 0,
          duration: 0.8,
          ease: 'power2.out',
          scrollTrigger: {
            start: 'top 82%',
            toggleActions: 'play none none reverse',
            trigger: element,
          },
          y: 44,
        })
      })

    }, root)

    const refreshId = window.setTimeout(() => ScrollTrigger.refresh(), 120)

    return () => {
      window.clearTimeout(refreshId)
      ctx.revert()
    }
  }, [])

  useEffect(() => {
    if (prefersReducedMotion()) {
      return
    }

    const startTime = window.performance.now()
    const duration = 1700

    const intervalId = window.setInterval(() => {
      const timestamp = window.performance.now()
      const progress = Math.min((timestamp - startTime) / duration, 1)
      const easedProgress = 1 - Math.pow(1 - progress, 3)
      const nextLength = Math.min(heroTitle.length, Math.floor(easedProgress * heroTitle.length))

      setVisibleHeroTitleLength(nextLength)
      setHeroTitleOpacity(Math.min(1, progress * 1.15))

      if (progress >= 1) {
        window.clearInterval(intervalId)
        setVisibleHeroTitleLength(heroTitle.length)
        setHeroTitleOpacity(1)
        setIsHeroTitleTyping(false)
      }
    }, 32)

    return () => window.clearInterval(intervalId)
  }, [])

  return (
    <div className="landing-page" ref={rootRef}>
      <canvas className="landing-dot-grid-background" ref={dotGridCanvasRef} aria-hidden="true" />
      <div className="landing-announcement">
        <span>lawdit keeps sensitive-data discovery tied to redacted evidence, accountable owners, and recorded decisions.</span>
        <a href="#safety" onClick={(event) => handleSectionLink(event, 'safety')}>
          Review boundaries <ArrowRight aria-hidden="true" size={14} />
        </a>
      </div>

      <header className="landing-nav-shell">
        <Link className="landing-brand" to="/">
          <img className="landing-brand-logo" src="/brand/lawdit-wordmark-light.svg?v=20260601-logo" alt="lawdit" />
        </Link>
        <nav className="landing-nav" aria-label="Homepage navigation">
          <a href="#try-analysis" onClick={(event) => handleSectionLink(event, 'try-analysis')}>Analyze file</a>
          <a href="#problem" onClick={(event) => handleSectionLink(event, 'problem')}>Problem</a>
          <a href="#workflow" onClick={(event) => handleSectionLink(event, 'workflow')}>Workflow</a>
          <a href="#sample" onClick={(event) => handleSectionLink(event, 'sample')}>Sources</a>
          <a href="#safety" onClick={(event) => handleSectionLink(event, 'safety')}>Safety</a>
        </nav>
        <Link className="landing-nav-cta" to="/dashboard">Open dashboard</Link>
      </header>

      <main>
        <section className="landing-hero" id="overview" tabIndex={-1}>
          <div className="landing-hero-scene" aria-hidden="true">
            <div className="landing-scene-grid" />
            <div
              className="landing-file-card landing-parallax-slow"
              onPointerLeave={handleHeroCardPointerLeave}
              onPointerMove={handleHeroCardPointerMove}
            >
              <div className="landing-card-face">
                <div className="landing-file-card-header">
                  <span>Configured source file</span>
                  <strong>Needs review</strong>
                </div>
                <p>Identifier: [REDACTED]</p>
                <p>Contact: [REDACTED_EMAIL]</p>
                <small>Evidence anchors stay masked</small>
              </div>
            </div>
            <div
              className="landing-route-card landing-parallax-medium"
              onPointerLeave={handleHeroCardPointerLeave}
              onPointerMove={handleHeroCardPointerMove}
            >
              <div className="landing-card-face">
                <span>Owner route</span>
                <strong>Accountable owner</strong>
                <div className="landing-route-graph">
                  <i /> <b /> <i />
                </div>
                <small>Assigned for human review</small>
              </div>
            </div>
            <div
              className="landing-audit-card landing-parallax-fast"
              onPointerLeave={handleHeroCardPointerLeave}
              onPointerMove={handleHeroCardPointerMove}
            >
              <div className="landing-card-face">
                <span>Audit trail</span>
                <p>scan started</p>
                <p>finding assigned</p>
                <p>review recorded</p>
              </div>
            </div>
          </div>

          <div className="landing-hero-copy">
            <h1
              aria-label={heroTitle}
              className="landing-hero-title"
              style={{ opacity: heroTitleOpacity }}
            >
              <span aria-hidden="true" className="landing-hero-title-text">
                {visibleHeroTitle}
                {isHeroTitleTyping ? <span className="landing-hero-title-caret" /> : null}
              </span>
              <span aria-hidden="true" className="landing-hero-title-measure">{heroTitle}</span>
            </h1>
            <p>
              Upload or connect controlled sources, inspect redacted evidence, route findings to accountable owners, record
              human decisions, and keep audit and evaluation signals visible.
            </p>
            <div className="landing-hero-actions">
              <a className="landing-primary landing-hero-primary" href="#try-analysis" onClick={(event) => handleSectionLink(event, 'try-analysis')}>
                <span className="landing-primary-content">
                  Analyze one file <ArrowRight aria-hidden="true" size={17} />
                </span>
              </a>
              <Link className="landing-secondary" to="/dashboard">Open dashboard</Link>
            </div>
          </div>

          <div className="landing-action-flow" aria-hidden="true">
            <svg viewBox="0 0 1180 210" preserveAspectRatio="none">
              <defs>
                <linearGradient id="landing-flow-gradient" x1="0%" x2="100%" y1="0%" y2="0%">
                  <stop offset="0%" stopColor="#0b57d0" stopOpacity="0" />
                  <stop offset="26%" stopColor="#0b57d0" stopOpacity=".28" />
                  <stop offset="52%" stopColor="#147a42" stopOpacity=".2" />
                  <stop offset="78%" stopColor="#62666c" stopOpacity=".18" />
                  <stop offset="100%" stopColor="#0b57d0" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path className="landing-flow-path" d="M18 118 C170 92 304 112 438 108 C520 106 548 88 604 88 C674 88 706 112 780 112 C914 112 1018 88 1162 104" />
              <path className="landing-flow-trace" d="M18 118 C170 92 304 112 438 108 C520 106 548 88 604 88 C674 88 706 112 780 112 C914 112 1018 88 1162 104" />
            </svg>
          </div>

        </section>

        <PublicAnalysisTrial />

        <section className="landing-feature-rail" aria-label="lawdit capabilities">
          {proofPoints.map(({ title, description, icon: Icon, tone }) => (
            <article className={`landing-proof landing-proof-${tone}`} key={title}>
              <Icon aria-hidden="true" size={20} strokeWidth={1.9} />
              <strong>{title}</strong>
              <p>{description}</p>
            </article>
          ))}
        </section>

        <section className="landing-section landing-problem" id="problem" tabIndex={-1}>
          <div className="landing-section-copy landing-reveal">
            <h2 className="landing-problem-title">
              <TrueFocus
                animationDuration={0.45}
                blurAmount={2.4}
                borderColor="rgba(11, 87, 208, .52)"
                glowColor="rgba(11, 87, 208, .14)"
                pauseBetweenAnimations={1.1}
                sentence="From detection to accountable action."
              />
            </h2>
            <p>
              A detector-only scan can find sensitive values but still leave ownership, permission boundaries, and proof
              unresolved. lawdit turns each signal into a review case with evidence, routing, action scope, and audit.
            </p>
          </div>
          <div className="landing-conversion-layout" aria-label="Scanner to governance comparison">
            <article className="landing-scanner-card landing-reveal">
              <div className="landing-problem-card-topline">
                <span>Detection only</span>
                <span>Incomplete</span>
              </div>
              <h3>Detector-only scan</h3>
              <p>Stops before accountability</p>
              <div className="landing-scanner-output">
                <strong>PII hits found:</strong>
                <ul>
                  {scannerHits.map((hit) => (
                    <li key={hit}>{hit}</li>
                  ))}
                </ul>
              </div>
              <div className="landing-scanner-missing">
                <strong>Missing:</strong>
                <ul>
                  {scannerMissingControls.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </article>

            <div className="landing-conversion-connector landing-reveal" aria-hidden="true">
              <span>Detection</span>
              <i><ArrowRight size={20} /></i>
              <span>Governance</span>
            </div>

            <article className="landing-governance-loop-card landing-reveal">
              <div className="landing-problem-card-topline">
                <span>Control plane</span>
                <span>Review case</span>
              </div>
              <h3>lawdit review workflow</h3>
              <p>Turns signals into accountable review records</p>
              <div className="landing-governance-loop">
                {governanceLoopSteps.map(([title, description], index) => (
                  <div className="landing-governance-loop-row" key={title}>
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    <div>
                      <strong>{title}</strong>
                      <p>{description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>
          <p className="landing-accountability-callout landing-reveal">
            Cleanup decisions stay gated. Human review remains explicit, justified, and auditable.
          </p>
        </section>

        <section className="landing-section landing-workflow" id="workflow" tabIndex={-1}>
          <div className="landing-workflow-depth-grid" aria-hidden="true" />
          <div className="landing-section-copy landing-reveal">
            <h2>From source files to accountable review.</h2>
            <p>
              lawdit is not a generic PII scanner or automatic deletion tool. The workflow keeps source readiness,
              redaction, ownership, review support, permission boundaries, audit events, delta scans, and evaluation visible.
            </p>
          </div>
          <div className="landing-workflow-layout">
            <div className="landing-workflow-visual landing-reveal" aria-hidden="true">
              <span className="landing-workflow-visual-hint">Click a phase for details</span>
              <div
                className="beam-wrapper"
                style={{
                  height: '100%',
                  left: 0,
                  maskImage: 'linear-gradient(to bottom, transparent 0%, transparent 18%, black 24%, black 84%, transparent 100%)',
                  overflow: 'hidden',
                  pointerEvents: 'none',
                  position: 'absolute',
                  top: 0,
                  WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, transparent 18%, black 24%, black 84%, transparent 100%)',
                  width: '100%',
                  zIndex: 1,
                }}
              >
                <style>{`
                  :root {
                    --beam-duration: 7s;
                    --beam-delay: 0s;
                    --beam-ease: cubic-bezier(0.4, 0, 0.2, 1);
                  }
                  @keyframes track-pulse {
                    0%, 100% { opacity: 0.04; }
                    50% { opacity: 0.16; }
                  }
                  @keyframes rail-glow-breathe {
                    0%, 100% {
                      opacity: 0.08;
                      transform: scale(1);
                    }
                    50% {
                      opacity: 0.2;
                      transform: scale(1.015);
                    }
                  }
                  .rail-breathe {
                    animation: rail-glow-breathe 6.5s ease-in-out infinite;
                    filter: blur(18px);
                    transform-box: fill-box;
                    transform-origin: center;
                  }
                  .rail-aura {
                    animation: track-pulse 4s ease-in-out infinite;
                    filter: blur(12px);
                  }
                  .rail-solid {
                    animation: track-pulse 4s ease-in-out infinite;
                  }
                  @keyframes beam-flow {
                    0% {
                      opacity: 0;
                      stroke-dashoffset: 2120;
                    }
                    8% {
                      opacity: 0;
                      stroke-dashoffset: 2120;
                    }
                    15% {
                      opacity: 1;
                      stroke-dashoffset: 2000;
                    }
                    65% {
                      opacity: 1;
                      stroke-dashoffset: 0;
                    }
                    75% {
                      opacity: 0;
                      stroke-dashoffset: -120;
                    }
                    100% {
                      opacity: 0;
                      stroke-dashoffset: -120;
                    }
                  }
                  .comet-flow {
                    animation: beam-flow var(--beam-duration) var(--beam-ease) var(--beam-delay) infinite;
                    opacity: 0;
                    stroke-dashoffset: 2120;
                  }
                  .comet-flow path {
                    stroke-dashoffset: inherit;
                  }
                  .comet-tail {
                    stroke-dasharray: 140 1860;
                    opacity: .76;
                    filter: blur(8px);
                  }
                  .comet-core {
                    stroke-dasharray: 140 1860;
                    opacity: .92;
                    filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.9));
                    transform: translate(0, 0);
                  }
                `}</style>

                <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none" style={{ minHeight: '800px', overflow: 'hidden' }}>
                  <g>
                    <path
                      d={workflowThreadPath}
                      fill="none"
                      stroke="#6D5DF6"
                      strokeWidth="22"
                      strokeLinecap="round"
                      className="rail-breathe"
                    />
                    <path
                      d={workflowThreadPath}
                      fill="none"
                      stroke="#4F46E5"
                      strokeWidth="12"
                      strokeLinecap="round"
                      className="rail-aura"
                    />
                    <path
                      d={workflowThreadPath}
                      fill="none"
                      stroke="#3B82F6"
                      strokeWidth="2"
                      strokeLinecap="round"
                      className="rail-solid"
                    />
                    <g className="comet-flow">
                      <path
                        d={workflowThreadPath}
                        fill="none"
                        stroke="#60A5FA"
                        strokeWidth="8"
                        strokeLinecap="round"
                        pathLength={2000}
                        className="comet-tail"
                      />
                      <path
                        d={workflowThreadPath}
                        fill="none"
                        stroke="#ffffff"
                        strokeWidth="2"
                        strokeLinecap="round"
                        pathLength={2000}
                        className="comet-core"
                      />
                    </g>
                  </g>
                </svg>
              </div>
              <div className="landing-workflow-phase-stack">
                {workflowNodeLabels.map((label, index) => (
                  <div className="landing-workflow-flow-item" key={label}>
                    <button
                      className={`landing-workflow-node${isWorkflowDetailOpen && visibleWorkflowNodeIndex === index ? ' landing-workflow-node-active' : ''}`}
                      type="button"
                      onClick={() => openWorkflowPhase(index)}
                      onFocus={() => setActiveWorkflowNodeIndex(index)}
                    >
                      <span>{label}</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <div className={`landing-workflow-steps-shell landing-reveal${isWorkflowDetailOpen ? ' landing-workflow-steps-shell-detail' : ' landing-workflow-steps-shell-overview'}`}>
              <div className="landing-workflow-steps" key={isWorkflowDetailOpen ? visibleWorkflowNodeIndex : 'overview'}>
                {!isWorkflowDetailOpen ? (
                  <>
                    <div className="landing-workflow-panel-top">
                      <span className="landing-workflow-phase-label">All workflow steps</span>
                    </div>
                    <div className="landing-workflow-overview-grid">
                      {workflowSteps.map((step, stepIndex) => {
                        const phaseIndex = workflowStepPhaseIndexes[stepIndex] ?? 0

                        return (
                          <button
                            className="landing-workflow-step landing-workflow-overview-step"
                            key={step.title}
                            onClick={() => openWorkflowStep(stepIndex)}
                            style={{ '--workflow-step-delay': `${stepIndex * 35}ms` } as CSSProperties}
                            type="button"
                          >
                            <span>{String(stepIndex + 1).padStart(2, '0')}</span>
                            <div>
                              <strong>{step.title}</strong>
                              <small>{workflowNodeLabels[phaseIndex]}</small>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </>
                ) : (
                  <>
                    <div className="landing-workflow-detail-header">
                      <div>
                        <span className="landing-workflow-phase-label">{visibleWorkflowPhase.title}</span>
                        <strong>{visibleWorkflowPhase.range}</strong>
                      </div>
                      <button className="landing-workflow-back" type="button" onClick={resetWorkflowPhase}>
                        All steps
                      </button>
                    </div>
                    <article className="landing-workflow-detail-summary">
                      <span>Phase objective</span>
                      <h3>{visibleWorkflowPhase.summary}</h3>
                      <dl>
                        <div>
                          <dt>Goal</dt>
                          <dd>{visibleWorkflowPhase.objective}</dd>
                        </div>
                        <div>
                          <dt>Output</dt>
                          <dd>{visibleWorkflowPhase.output}</dd>
                        </div>
                      </dl>
                    </article>
                    <div className="landing-workflow-detail-step-grid">
                      {visibleWorkflowPhase.stepIndexes.map((stepIndex, index) => {
                        const step = workflowSteps[stepIndex]

                        return (
                          <article
                            className="landing-workflow-detail-step"
                            key={step.title}
                            style={{ '--workflow-step-delay': `${index * 70}ms` } as CSSProperties}
                          >
                            <span>{String(stepIndex + 1).padStart(2, '0')}</span>
                            <div>
                              <strong>{step.title}</strong>
                              <p>{step.description}</p>
                              <small>{visibleWorkflowPhase.title} phase</small>
                            </div>
                          </article>
                        )
                      })}
                    </div>
                    <div className="landing-workflow-detail-footer">
                      <button
                        className="landing-workflow-phase-control"
                        disabled={visibleWorkflowNodeIndex === 0}
                        type="button"
                        onClick={selectPreviousWorkflowPhase}
                      >
                        Previous phase
                      </button>
                      <div className="landing-workflow-mini-timeline" aria-label="Workflow phase progress">
                        {workflowPhases.map((phase, index) => (
                          <button
                            aria-label={`Show ${phase.title} phase`}
                            className={index === visibleWorkflowNodeIndex ? 'landing-workflow-mini-dot-active' : ''}
                            key={phase.id}
                            type="button"
                            onClick={() => openWorkflowPhase(index)}
                          />
                        ))}
                      </div>
                      <button
                        className="landing-workflow-phase-control"
                        disabled={visibleWorkflowNodeIndex === workflowPhases.length - 1}
                        type="button"
                        onClick={selectNextWorkflowPhase}
                      >
                        Next phase
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="landing-section landing-sample" id="sample" tabIndex={-1}>
          <div className="landing-section-copy landing-reveal">
            <h2>Start with an explicit source.</h2>
            <p>
              The console treats source registration as the boundary before scanning. The organizer sample repository remains
              the default validation reference without copying its files into this repository.
            </p>
          </div>
          <div className="landing-sample-layout">
            <article className="landing-sample-card landing-reveal">
              <span>Optional validation reference</span>
              <strong>Organizer GDPR Data Samples</strong>
              <a href="https://github.com/a-klumpp/GDPR-data-samples" rel="noreferrer" target="_blank">
                Open reference dataset <ExternalLink aria-hidden="true" size={14} />
              </a>
            </article>
            <div className="landing-sample-families landing-reveal" aria-label="Sample families">
              {sampleFamilies.map((family) => <span key={family}>{family}</span>)}
            </div>
          </div>
        </section>

        <section className="landing-section landing-governance" id="governance" tabIndex={-1}>
          <div className="landing-governance-copy landing-reveal">
            <h2>Governance stays configurable.</h2>
            <p>
              Versioned policy packs, organization models, permission boundaries, reviewer guidance, and escalation choices
              stay visible instead of being hard-coded into detector logic.
            </p>
          </div>
          <div className="landing-console-preview">
            <aside className={`landing-policy-selector landing-reveal${isGovernanceFolderOpen ? ' landing-policy-selector-open' : ''}`} aria-label="Policy pack files">
              <div className="landing-policy-selector-top">
                <div>
                  <span>Policy pack</span>
                  <strong>Governance files</strong>
                </div>
                <b className="landing-policy-selector-count">
                  {String(activeGovernanceIndex + 1).padStart(2, '0')} / {String(governanceCards.length).padStart(2, '0')}
                </b>
              </div>
              <button
                aria-label="Preview policy pack folder"
                className="landing-policy-mini-folder"
                type="button"
                onClick={() => setIsGovernanceFolderOpen((current) => !current)}
                onMouseEnter={() => setIsGovernanceFolderOpen(true)}
                onMouseLeave={() => setIsGovernanceFolderOpen(false)}
              >
                <span className="landing-policy-mini-folder-back">
                  {governanceLayerLabels.slice(0, 3).map((label, index) => (
                    <i className={`landing-policy-mini-paper landing-policy-mini-paper-${index + 1}`} key={label}>
                      {label}
                    </i>
                  ))}
                  <span className="landing-policy-mini-folder-front">
                    <b>Policy pack</b>
                    <small>{governanceLayerLabels[activeGovernanceIndex]}</small>
                  </span>
                </span>
              </button>
              <div className="landing-policy-selector-files" aria-label="Governance files">
                {governanceLayerLabels.map((label, index) => (
                  <button
                    aria-pressed={index === activeGovernanceIndex}
                    className={index === activeGovernanceIndex ? 'landing-policy-selector-file-active' : ''}
                    key={label}
                    type="button"
                    onClick={() => selectGovernanceCard(index)}
                  >
                    <span>{label}</span>
                    <small>{governanceCards[index].title}</small>
                  </button>
                ))}
              </div>
              <div className="landing-policy-selector-dots" aria-hidden="true">
                {governanceCards.map((card, index) => (
                  <span className={index === activeGovernanceIndex ? 'landing-policy-selector-dot-active' : ''} key={card.title} />
                ))}
              </div>
            </aside>
            <div className="landing-governance-main landing-reveal" aria-live="polite">
              <div className="landing-governance-card-stack">
                {governanceCards.slice(1).map((card, index) => (
                  <span
                    className={`landing-governance-stack-shadow landing-governance-stack-shadow-${index + 1}`}
                    key={`${card.title}-shadow`}
                  />
                ))}
                <article className="landing-governance-active-card" key={activeGovernanceCard.title}>
                  <div className="landing-governance-card-heading">
                    <span>Active policy layer</span>
                    <strong>{activeGovernanceCard.title}</strong>
                  </div>
                  <div className="landing-governance-active-content">
                    {renderGovernanceCardContent(activeGovernanceCard, true)}
                  </div>
                </article>
              </div>
            </div>
            <div className="landing-console-copy landing-reveal">
              <strong>Open the governed console.</strong>
              <p>
                The console starts at /dashboard and keeps public one-file analysis separate from the governed review Workspace.
              </p>
              <Link className="landing-primary" to="/dashboard">
                Open dashboard <ArrowRight aria-hidden="true" size={17} />
              </Link>
            </div>
          </div>
        </section>

        <section className="landing-section landing-evaluation" id="evaluation" tabIndex={-1}>
          <div className="landing-evaluation-copy landing-reveal">
            <h2>Every file has a visible status.</h2>
            <p>
              Each finding moves through a governed lifecycle: detected, assigned, reviewed, decided, audited, and monitored by
              delta scans.
            </p>
          </div>
          <div
            aria-label="File status lifecycle gallery"
            className={`landing-file-status-gallery landing-reveal${isFileStatusDragging ? ' landing-file-status-gallery-dragging' : ''}`}
            role="region"
            onMouseEnter={() => setIsFileStatusHovered(true)}
            onMouseLeave={() => setIsFileStatusHovered(false)}
            onPointerCancel={handleFileStatusPointerEnd}
            onPointerDown={handleFileStatusPointerDown}
            onPointerMove={handleFileStatusPointerMove}
            onPointerUp={handleFileStatusPointerEnd}
            onWheel={handleFileStatusWheel}
          >
            <div className="landing-file-status-stage">
              {fileStatusCards.map((status, index) => {
                const position = getFileStatusPosition(index)
                const absPosition = Math.min(Math.abs(position), 3)
                const isActive = index === activeFileStatusIndex && Math.abs(fileStatusDragOffset) < 36

                return (
                  <article
                    aria-hidden={Math.abs(position) > 2.75}
                    className={`landing-file-status-card landing-file-status-card-${status.tone}${isActive ? ' landing-file-status-card-active' : ''}`}
                    key={status.id}
                    role="button"
                    style={{
                      '--status-arc-y': `${absPosition * absPosition * 18}px`,
                      '--status-opacity': `${Math.max(0.34, 1 - absPosition * 0.22)}`,
                      '--status-position': position,
                      '--status-rotate': `${position * -5.4}deg`,
                      '--status-scale': `${Math.max(0.72, 1 - absPosition * 0.105)}`,
                      zIndex: 20 - Math.round(absPosition * 4),
                    } as CSSProperties}
                    tabIndex={Math.abs(position) <= 2.75 ? 0 : -1}
                    onClick={() => {
                      if (!fileStatusDidDragRef.current) {
                        selectFileStatus(index)
                      }
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        selectFileStatus(index)
                      }
                    }}
                  >
                    <div className="landing-file-status-card-top">
                      <span>{status.eyebrow}</span>
                      <b>{String(index + 1).padStart(2, '0')}</b>
                    </div>
                    <strong>{status.title}</strong>
                    <p>{status.description}</p>
                    <div className="landing-file-status-meta">
                      {status.meta.map((item) => {
                        const [label, value] = item.split(': ')

                        return (
                          <span key={item}>
                            <small>{label}</small>
                            <em>{value}</em>
                          </span>
                        )
                      })}
                    </div>
                  </article>
                )
              })}
            </div>
            <div className="landing-file-status-indicator">
              <strong>{activeFileStatus.title}</strong>
              <span>
                {String(activeFileStatusIndex + 1).padStart(2, '0')} / {String(fileStatusCards.length).padStart(2, '0')}
              </span>
              <div aria-label="Select file status" className="landing-file-status-dots">
                {fileStatusCards.map((status, index) => (
                  <button
                    aria-label={`Show ${status.title} status`}
                    className={index === activeFileStatusIndex ? 'landing-file-status-dot-active' : ''}
                    key={`${status.id}-dot`}
                    type="button"
                    onClick={() => selectFileStatus(index)}
                  />
                ))}
              </div>
            </div>
            <p className="landing-file-status-hint">Drag or scroll to inspect the governed file lifecycle.</p>
          </div>
        </section>

        <section className="landing-section landing-safety" id="safety" tabIndex={-1}>
          <div className="landing-section-copy landing-reveal">
            <h2>Safe operating boundaries stay visible.</h2>
            <p>
              The public homepage and Workspace avoid raw sensitive content, legal advice, full-compliance claims,
              automatic deletion, and production integration promises.
            </p>
          </div>
          <div className="landing-safety-grid">
            {safetyBoundaries.map(({ title, description, icon: Icon }) => (
              <article className="landing-safety-card landing-reveal" key={title}>
                <Icon aria-hidden="true" size={24} />
                <strong>{title}</strong>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-final">
          <h2>Open the lawdit console.</h2>
          <Link className="landing-primary" to="/dashboard">
            Open dashboard <ArrowRight aria-hidden="true" size={17} />
          </Link>
        </section>
      </main>
    </div>
  )
}
