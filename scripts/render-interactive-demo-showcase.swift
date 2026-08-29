import AppKit
import AVFoundation
import CoreVideo
import Darwin
import Foundation
import WebKit

final class InteractiveShowcase: NSObject, WKNavigationDelegate {
    private let repository = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    private let artifacts: URL
    private let outputURL: URL
    private let silentURL: URL
    private let narrationURL: URL
    private let canvas = CGSize(width: 1920, height: 1080)
    private let outputFPS: Int32 = 30
    private let captureFPS = 6
    private let duration: Double
    private let webView: WKWebView
    private let window: NSWindow
    private let writer: AVAssetWriter
    private let input: AVAssetWriterInput
    private let adapter: AVAssetWriterInputPixelBufferAdaptor
    private var sampleIndex = 0
    private var frameIndex: Int64 = 0
    private var hasStarted = false

    override init() {
        artifacts = repository.appendingPathComponent("artifacts/demo-video")
        outputURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-Demo.mp4")
        silentURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-silent.mp4")
        narrationURL = URL(fileURLWithPath: ProcessInfo.processInfo.environment["VICE_CEO_NARRATION_PATH"] ?? artifacts.appendingPathComponent("vice-ceo-demo-narration.mp3").path)
        let narration = AVURLAsset(url: narrationURL)
        let narrationDuration = CMTimeGetSeconds(narration.duration)
        duration = narrationDuration.isFinite && narrationDuration > 0 ? narrationDuration + 0.5 : 173

        let webFrame = NSRect(x: 0, y: 0, width: 1728, height: 940)
        window = NSWindow(contentRect: webFrame, styleMask: [.titled], backing: .buffered, defer: false)
        webView = WKWebView(frame: webFrame)
        window.contentView = webView

        try! FileManager.default.createDirectory(at: artifacts, withIntermediateDirectories: true)
        if FileManager.default.fileExists(atPath: silentURL.path) { try! FileManager.default.removeItem(at: silentURL) }
        if FileManager.default.fileExists(atPath: outputURL.path) { try! FileManager.default.removeItem(at: outputURL) }
        writer = try! AVAssetWriter(outputURL: silentURL, fileType: .mp4)
        input = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.h264,
            AVVideoWidthKey: canvas.width,
            AVVideoHeightKey: canvas.height,
            AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 9_000_000]
        ])
        input.expectsMediaDataInRealTime = false
        adapter = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
            kCVPixelBufferWidthKey as String: canvas.width,
            kCVPixelBufferHeightKey as String: canvas.height,
            kCVPixelBufferCGImageCompatibilityKey as String: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey as String: true
        ])
        super.init()
        webView.navigationDelegate = self
        window.orderOut(nil)
    }

    func start() throws {
        guard writer.canAdd(input) else { throw NSError(domain: "ViceCEOShowcase", code: 1) }
        writer.add(input)
        writer.startWriting()
        writer.startSession(atSourceTime: .zero)
        let url = URL(string: "https://vice-ceo-review-demo-77u4kmu2ba-uc.a.run.app/demo")!
        webView.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData))
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        guard !hasStarted else { return }
        hasStarted = true
        renderNextSample()
    }

    private func stateScript(at time: Double) -> String {
        let selector: String
        let scroll: Int
        let cursor: CGPoint
        let receipt: String
        let scene: (kicker: String, title: String, detail: String, chips: [String], visible: Bool)

        switch time {
        case ..<10:
            selector = ".intro"
            scroll = 0
            cursor = CGPoint(x: 530 + time * 22, y: 330 + time * 9)
            receipt = "hide"
            scene = ("PROOF-CARRYING BUSINESS AUTONOMY", "Your business\nshould not run\non sticky notes.", "Vice CEO turns routine communication and follow-through into work that is already moving.", ["Observe", "Decide", "Prepare"], true)
        case ..<30:
            selector = "[data-action=send_customer_reply]"
            scroll = 0
            let phase = min(max((time - 10) / 8, 0), 1)
            cursor = CGPoint(x: 520 + phase * 650, y: 540 + phase * 300)
            receipt = time >= 21 ? "reply" : "hide"
            scene = ("CUSTOMER SUPPORT", "Routine help.\nAlready handled.", "Vice CEO matches approved policy, prepares the response, and keeps the original customer context attached.", ["Policy matched", "Reply prepared", "Receipt created"], time >= 10 && time < 14)
        case ..<48:
            selector = "[data-action=send_outreach_follow_up]"
            scroll = 0
            let phase = min(max((time - 30) / 8, 0), 1)
            cursor = CGPoint(x: 1090 + phase * 480, y: 610 + phase * 220)
            receipt = time >= 41 ? "followup" : "hide"
            scene = ("APPROVED OUTREACH", "The next step\nnever gets lost.", "Consent-aware follow-through stays ready, stops on reply or unsubscribe, and never repeats itself.", ["Approved campaign", "Consent-aware", "Duplicate-safe"], time >= 30 && time < 34)
        case ..<66:
            selector = "#activity"
            scroll = 430
            cursor = CGPoint(x: 835, y: 550)
            receipt = "hide"
            scene = ("THE HUMAN MOMENT", "Escalate judgment.\nNot workload.", "When the work needs empathy or a real business decision, Vice CEO gathers the facts and brings in the right person.", ["Knows the difference", "Focused decision", "No messy thread"], time >= 48 && time < 53)
        case ..<86:
            selector = ".work-item.selected"
            scroll = 190
            cursor = CGPoint(x: 350, y: 470)
            receipt = time >= 78 ? "reply" : "hide"
            scene = ("WORK YOU CAN TRUST", "No black box.\nJust receipts.", "Every action carries its source, policy, decision, and delivery state—so the owner can understand what happened.", ["Source", "Policy", "Decision", "Outcome"], time >= 66 && time < 71)
        case ..<106:
            selector = ".activity-item:nth-child(3)"
            scroll = 520
            cursor = CGPoint(x: 1030, y: 500)
            receipt = "hide"
            scene = ("AUTHORITY IS EARNED", "You choose\nhow much it can do.", "Start with preparation. Enable delivery only for the work and systems your business approves.", ["Prepare", "Review", "Enable"], time >= 86 && time < 91)
        case ..<132:
            selector = ".campaign"
            scroll = 190
            cursor = CGPoint(x: 1510, y: 530)
            receipt = time >= 121 ? "followup" : "hide"
            scene = ("WESTOVER EPR", "A real business\noperator pattern.", "Registry signals, customer service, and approved outreach all become organized follow-through instead of another inbox.", ["Registry signals", "Customer work", "Follow-through"], time >= 106 && time < 111)
        case ..<155:
            selector = ".live-note"
            scroll = 575
            cursor = CGPoint(x: 880, y: 675)
            receipt = "hide"
            scene = ("BUILT FOR REAL WORK", "Useful before\nit is impressive.", "Vice CEO works quietly in the background and surfaces only the decisions that deserve a person’s attention.", ["Background work", "Clear handoffs", "Business control"], time >= 132 && time < 137)
        default:
            selector = ".intro"
            scroll = 0
            cursor = CGPoint(x: -60, y: -60)
            receipt = "hide"
            scene = ("VICE CEO", "Less chasing.\nMore running\nthe business.", "A behind-the-scenes business operator for the repeatable work that never stops.", ["Customer service", "Follow-through", "Proof"], true)
        }

        let resultScript: String
        switch receipt {
        case "reply":
            resultScript = "showResult('success', 'Reply prepared', 'Vice CEO prepared this work. It can send through the business mailbox when you choose to enable that authority.', 'business_receipt_demo_reply · consent and source policy verified');"
        case "followup":
            resultScript = "showResult('success', 'Follow-up prepared', 'Vice CEO prepared the next touch for a consented lead. It stops automatically on reply or unsubscribe.', 'business_receipt_demo_follow_up · duplicate protection enabled');"
        default:
            resultScript = "result.className = 'result';"
        }

        let slideMarkup: String
        if scene.visible {
            let chips = scene.chips.map { "<span>\($0)</span>" }.joined()
            slideMarkup = """
            <section class="vice-ceo-slide" aria-label="Vice CEO product story">
              <div class="vice-ceo-slide-grid"></div>
              <div class="vice-ceo-slide-orbit vice-ceo-slide-orbit-one"></div>
              <div class="vice-ceo-slide-orbit vice-ceo-slide-orbit-two"></div>
              <div class="vice-ceo-slide-content">
                <div class="vice-ceo-slide-kicker"><i></i> \(scene.kicker)</div>
                <h1>\(scene.title.replacingOccurrences(of: "\\n", with: "<br>"))</h1>
                <p>\(scene.detail)</p>
                <div class="vice-ceo-slide-chips">\(chips)</div>
              </div>
              <div class="vice-ceo-slide-signature"><b>VC</b><span>VICE CEO<br><em>BUSINESS AUTONOMY</em></span></div>
            </section>
            """
        } else {
            slideMarkup = ""
        }

        return """
        (() => {
          const styleId = 'vice-ceo-showcase-style';
          if (!document.getElementById(styleId)) {
            const style = document.createElement('style');
            style.id = styleId;
            style.textContent = `
              .tour-focus { box-shadow:0 0 0 4px rgba(18,79,59,.22),0 18px 34px rgba(18,79,59,.15)!important; position:relative; z-index:3; }
              #vice-ceo-tour-cursor { position:fixed; width:27px; height:27px; margin:-13px 0 0 -13px; border:3px solid #124f3b; border-radius:50%; background:rgba(255,255,255,.92); box-shadow:0 3px 12px rgba(18,79,59,.25); z-index:9999; pointer-events:none; transition:none; }
              #vice-ceo-tour-cursor::after { content:''; display:block; width:7px; height:7px; margin:7px; border-radius:50%; background:#6cc8a7; }
              #vice-ceo-showcase-scene { position:fixed; inset:0; z-index:9998; pointer-events:none; }
              .vice-ceo-slide { position:absolute; inset:0; overflow:hidden; color:#f6f1e7; background:linear-gradient(132deg,#08241d 0%,#0d3d30 54%,#1c7259 130%); font-family:ui-sans-serif,system-ui,-apple-system,sans-serif; }
              .vice-ceo-slide::after { content:''; position:absolute; inset:0; background:radial-gradient(circle at 76% 28%,rgba(173,236,201,.18),transparent 27%),radial-gradient(circle at 25% 85%,rgba(255,255,255,.08),transparent 31%); }
              .vice-ceo-slide-grid { position:absolute; inset:-1px; opacity:.26; background-image:linear-gradient(rgba(226,247,233,.19) 1px,transparent 1px),linear-gradient(90deg,rgba(226,247,233,.19) 1px,transparent 1px); background-size:56px 56px; mask-image:linear-gradient(90deg,#000,transparent 73%); }
              .vice-ceo-slide-orbit { position:absolute; border:1px solid rgba(207,246,220,.35); border-radius:50%; }
              .vice-ceo-slide-orbit-one { width:710px; height:710px; right:-170px; top:-230px; box-shadow:0 0 0 48px rgba(207,246,220,.04),0 0 0 110px rgba(207,246,220,.025); }
              .vice-ceo-slide-orbit-two { width:400px; height:400px; right:55px; top:-65px; border-color:rgba(207,246,220,.17); }
              .vice-ceo-slide-content { position:absolute; z-index:2; left:144px; top:50%; width:890px; transform:translateY(-50%); }
              .vice-ceo-slide-kicker { display:flex; align-items:center; gap:11px; color:#bce8cb; font-size:15px; font-weight:800; letter-spacing:.16em; }
              .vice-ceo-slide-kicker i { width:11px; height:11px; border-radius:50%; background:#8be0ae; box-shadow:0 0 0 8px rgba(139,224,174,.13); }
              .vice-ceo-slide h1 { margin:24px 0 22px; color:#f8f4eb; text-shadow:0 3px 18px rgba(0,0,0,.16); font-size:76px; line-height:.98; letter-spacing:-.065em; font-weight:760; }
              .vice-ceo-slide p { margin:0; max-width:690px; color:rgba(246,241,231,.81); font-size:25px; line-height:1.42; letter-spacing:-.02em; }
              .vice-ceo-slide-chips { display:flex; gap:12px; flex-wrap:wrap; margin-top:34px; }
              .vice-ceo-slide-chips span { padding:10px 14px; border:1px solid rgba(230,248,236,.33); border-radius:999px; color:#e7f8eb; background:rgba(9,44,34,.28); font-size:14px; font-weight:700; }
              .vice-ceo-slide-signature { position:absolute; z-index:2; right:82px; bottom:70px; display:flex; align-items:center; gap:11px; color:#e3f4e7; font-size:15px; font-weight:780; line-height:1.05; letter-spacing:.04em; }
              .vice-ceo-slide-signature b { display:grid; place-items:center; width:39px; height:39px; border-radius:12px; background:#dff4e5; color:#0c4333; font-size:13px; }
              .vice-ceo-slide-signature em { color:#a9d7b9; font-size:9px; font-style:normal; font-weight:750; letter-spacing:.13em; }
            `;
            document.head.appendChild(style);
            const cursor = document.createElement('div'); cursor.id = 'vice-ceo-tour-cursor'; document.body.appendChild(cursor);
            const scene = document.createElement('div'); scene.id = 'vice-ceo-showcase-scene'; document.body.appendChild(scene);
          }
          document.querySelectorAll('.tour-focus').forEach((node) => node.classList.remove('tour-focus'));
          const target = document.querySelector('\(selector)'); if (target) target.classList.add('tour-focus');
          window.scrollTo(0, \(scroll));
          const cursor = document.getElementById('vice-ceo-tour-cursor'); cursor.style.left = '\(Int(cursor.x))px'; cursor.style.top = '\(Int(cursor.y))px';
          document.getElementById('vice-ceo-showcase-scene').innerHTML = `\(slideMarkup)`;
          \(resultScript)
        })();
        """
    }

    private func renderNextSample() {
        let sampleCount = Int(ceil(duration * Double(captureFPS)))
        guard sampleIndex < sampleCount else { finishVideo(); return }
        let time = Double(sampleIndex) / Double(captureFPS)
        webView.evaluateJavaScript(stateScript(at: time)) { [self] _, error in
            guard error == nil else { fail("Could not prepare live demo state: \(String(describing: error))"); return }
            DispatchQueue.main.async { [self] in
                let configuration = WKSnapshotConfiguration()
                configuration.rect = webView.bounds
                configuration.snapshotWidth = 1728
                webView.takeSnapshot(with: configuration) { [self] image, error in
                    guard let image, error == nil else { fail("Could not capture live demo: \(String(describing: error))"); return }
                    do {
                        try append(image: image, repeats: outputFPS / Int32(captureFPS))
                        sampleIndex += 1
                        renderNextSample()
                    } catch { fail("Could not encode live demo frame: \(error)") }
                }
            }
        }
    }

    private func append(image: NSImage, repeats: Int32) throws {
        for _ in 0..<repeats {
            while !input.isReadyForMoreMediaData { usleep(1_000) }
            guard let pool = adapter.pixelBufferPool else { throw NSError(domain: "ViceCEOShowcase", code: 2) }
            var buffer: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, pool, &buffer)
            guard let buffer else { throw NSError(domain: "ViceCEOShowcase", code: 3) }
            CVPixelBufferLockBaseAddress(buffer, [])
            guard let base = CVPixelBufferGetBaseAddress(buffer),
                  let context = CGContext(data: base, width: Int(canvas.width), height: Int(canvas.height), bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue) else {
                CVPixelBufferUnlockBaseAddress(buffer, [])
                throw NSError(domain: "ViceCEOShowcase", code: 4)
            }
            let graphics = NSGraphicsContext(cgContext: context, flipped: false)
            NSGraphicsContext.saveGraphicsState()
            NSGraphicsContext.current = graphics
            NSColor(calibratedRed: 0.035, green: 0.075, blue: 0.066, alpha: 1).setFill()
            NSBezierPath(rect: NSRect(origin: .zero, size: canvas)).fill()
            let scale = max(canvas.width / image.size.width, canvas.height / image.size.height)
            let size = CGSize(width: image.size.width * scale, height: image.size.height * scale)
            image.draw(in: NSRect(x: (canvas.width - size.width) / 2, y: (canvas.height - size.height) / 2, width: size.width, height: size.height), from: .zero, operation: .sourceOver, fraction: 1)
            NSGraphicsContext.restoreGraphicsState()
            CVPixelBufferUnlockBaseAddress(buffer, [])
            guard adapter.append(buffer, withPresentationTime: CMTime(value: frameIndex, timescale: outputFPS)) else { throw writer.error ?? NSError(domain: "ViceCEOShowcase", code: 5) }
            frameIndex += 1
        }
    }

    private func finishVideo() {
        input.markAsFinished()
        writer.finishWriting { [self] in
            DispatchQueue.main.async {
                do {
                    guard self.writer.status == .completed else { throw self.writer.error ?? NSError(domain: "ViceCEOShowcase", code: 6) }
                    try self.addNarration()
                    print("Rendered \(self.outputURL.path)")
                    NSApp.terminate(nil)
                } catch { self.fail("Could not finish live demo: \(error)") }
            }
        }
    }

    private func addNarration() throws {
        guard FileManager.default.fileExists(atPath: narrationURL.path) else { try FileManager.default.copyItem(at: silentURL, to: outputURL); return }
        let video = AVURLAsset(url: silentURL)
        let audio = AVURLAsset(url: narrationURL)
        let mix = AVMutableComposition()
        guard let sourceVideo = video.tracks(withMediaType: .video).first,
              let sourceAudio = audio.tracks(withMediaType: .audio).first,
              let destinationVideo = mix.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid),
              let destinationAudio = mix.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else { throw NSError(domain: "ViceCEOShowcase", code: 7) }
        try destinationVideo.insertTimeRange(CMTimeRange(start: .zero, duration: video.duration), of: sourceVideo, at: .zero)
        try destinationAudio.insertTimeRange(CMTimeRange(start: .zero, duration: min(video.duration, audio.duration)), of: sourceAudio, at: .zero)
        guard let export = AVAssetExportSession(asset: mix, presetName: AVAssetExportPresetHighestQuality) else { throw NSError(domain: "ViceCEOShowcase", code: 8) }
        export.outputURL = outputURL
        export.outputFileType = .mp4
        let done = DispatchSemaphore(value: 0)
        export.exportAsynchronously { done.signal() }
        done.wait()
        guard export.status == .completed else { throw export.error ?? NSError(domain: "ViceCEOShowcase", code: 9) }
    }

    private func fail(_ message: String) {
        fputs("Showcase render failed: \(message)\n", stderr)
        NSApp.terminate(nil)
        exit(1)
    }
}

do {
    let app = NSApplication.shared
    app.setActivationPolicy(.accessory)
    let showcase = InteractiveShowcase()
    try showcase.start()
    app.run()
} catch {
    fputs("Showcase render failed: \(error)\n", stderr)
    exit(1)
}
