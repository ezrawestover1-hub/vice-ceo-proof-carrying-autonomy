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

        switch time {
        case ..<12:
            selector = ".intro"
            scroll = 0
            cursor = CGPoint(x: 530 + time * 22, y: 330 + time * 9)
            receipt = "hide"
        case ..<34:
            selector = "[data-action=send_customer_reply]"
            scroll = 0
            let phase = min(max((time - 12) / 8, 0), 1)
            cursor = CGPoint(x: 520 + phase * 650, y: 540 + phase * 300)
            receipt = time >= 23 ? "reply" : "hide"
        case ..<56:
            selector = "[data-action=send_outreach_follow_up]"
            scroll = 0
            let phase = min(max((time - 34) / 8, 0), 1)
            cursor = CGPoint(x: 1090 + phase * 480, y: 610 + phase * 220)
            receipt = time >= 45 ? "followup" : "hide"
        case ..<78:
            selector = "#activity"
            scroll = 430
            cursor = CGPoint(x: 835, y: 550)
            receipt = "hide"
        case ..<100:
            selector = ".work-item.selected"
            scroll = 190
            cursor = CGPoint(x: 350, y: 470)
            receipt = time >= 89 ? "reply" : "hide"
        case ..<122:
            selector = ".activity-item:nth-child(3)"
            scroll = 520
            cursor = CGPoint(x: 1030, y: 500)
            receipt = "hide"
        case ..<146:
            selector = ".campaign"
            scroll = 190
            cursor = CGPoint(x: 1510, y: 530)
            receipt = time >= 134 ? "followup" : "hide"
        case ..<162:
            selector = ".live-note"
            scroll = 575
            cursor = CGPoint(x: 880, y: 675)
            receipt = "hide"
        default:
            selector = ".intro"
            scroll = 0
            cursor = CGPoint(x: -60, y: -60)
            receipt = "hide"
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
              #vice-ceo-showcase-chip { position:fixed; top:18px; left:20px; z-index:9998; padding:8px 11px; border-radius:999px; background:rgba(18,79,59,.93); color:#fff; font:700 11px/1 system-ui; letter-spacing:.08em; }
            `;
            document.head.appendChild(style);
            const cursor = document.createElement('div'); cursor.id = 'vice-ceo-tour-cursor'; document.body.appendChild(cursor);
            const chip = document.createElement('div'); chip.id = 'vice-ceo-showcase-chip'; chip.textContent = 'LIVE PRODUCT TOUR'; document.body.appendChild(chip);
          }
          document.querySelectorAll('.tour-focus').forEach((node) => node.classList.remove('tour-focus'));
          const target = document.querySelector('\(selector)'); if (target) target.classList.add('tour-focus');
          window.scrollTo(0, \(scroll));
          const cursor = document.getElementById('vice-ceo-tour-cursor'); cursor.style.left = '\(Int(cursor.x))px'; cursor.style.top = '\(Int(cursor.y))px';
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
