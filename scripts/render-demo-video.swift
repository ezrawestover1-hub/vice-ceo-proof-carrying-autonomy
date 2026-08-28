import AppKit
import AVFoundation
import CoreVideo
import Darwin
import Foundation

enum Motif { case signals, agents, outreach, escalation, receipt, cloud, closing }
struct Scene { let imagePath: String?; let eyebrow: String; let headline: String; let motif: Motif; let weight: Double }

let repository = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let artifacts = repository.appendingPathComponent("artifacts/demo-video")
let captures = artifacts.appendingPathComponent("captures")
let outputURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-Demo.mp4")
let silentURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-silent.mp4")
let narrationURL = URL(fileURLWithPath: ProcessInfo.processInfo.environment["VICE_CEO_NARRATION_PATH"] ?? artifacts.appendingPathComponent("vice-ceo-demo-narration.mp3").path)
let scenes = [
    Scene(imagePath: nil, eyebrow: "VICE CEO", headline: "The work behind the work.", motif: .signals, weight: 28),
    Scene(imagePath: nil, eyebrow: "BACKGROUND AUTONOMY", headline: "Signals become next steps.", motif: .signals, weight: 30),
    Scene(imagePath: captures.appendingPathComponent("reviewer-evidence.png").path, eyebrow: "EVIDENCE, NOT NOISE", headline: "See what changed. Know why it matters.", motif: .signals, weight: 31),
    Scene(imagePath: nil, eyebrow: "AGENTIC BY DESIGN", headline: "Specialists move work forward.", motif: .agents, weight: 32),
    Scene(imagePath: captures.appendingPathComponent("reviewer-home.png").path, eyebrow: "CUSTOMER MOMENTUM", headline: "Routine work keeps moving.", motif: .outreach, weight: 31),
    Scene(imagePath: captures.appendingPathComponent("reviewer-boundaries.png").path, eyebrow: "HUMAN JUDGMENT", headline: "Exceptions arrive with context.", motif: .escalation, weight: 30),
    Scene(imagePath: captures.appendingPathComponent("reviewer-evidence.png").path, eyebrow: "PROOF-CARRYING ACTION", headline: "Every decision leaves a receipt.", motif: .receipt, weight: 30),
    Scene(imagePath: repository.appendingPathComponent("ARCHITECTURE.png").path, eyebrow: "BUILT TO RUN", headline: "Durable work. Clear authority.", motif: .cloud, weight: 31),
    Scene(imagePath: nil, eyebrow: "VICE CEO", headline: "Open it to see what it handled.", motif: .closing, weight: 27)
]

let canvas = CGSize(width: 1920, height: 1080)
let fps: Int32 = 30
let ink = NSColor(calibratedRed: 0.025, green: 0.053, blue: 0.047, alpha: 1)
let forest = NSColor(calibratedRed: 0.040, green: 0.196, blue: 0.153, alpha: 1)
let moss = NSColor(calibratedRed: 0.160, green: 0.470, blue: 0.345, alpha: 1)
let mint = NSColor(calibratedRed: 0.570, green: 0.930, blue: 0.770, alpha: 1)
let sand = NSColor(calibratedRed: 0.940, green: 0.895, blue: 0.790, alpha: 1)
let coral = NSColor(calibratedRed: 0.965, green: 0.550, blue: 0.420, alpha: 1)

func duration() -> Double { let value = CMTimeGetSeconds(AVURLAsset(url: narrationURL).duration); return value.isFinite && value > 0 ? value + 0.5 : 173 }
func ease(_ value: CGFloat) -> CGFloat { 1 - pow(1 - min(max(value, 0), 1), 3) }
func pulse(_ seconds: Double, rate: Double = 1) -> CGFloat { CGFloat((sin(seconds * rate * .pi * 2) + 1) / 2) }
func round(_ rect: NSRect, _ radius: CGFloat, _ color: NSColor) { color.setFill(); NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius).fill() }
func outline(_ rect: NSRect, _ radius: CGFloat, _ color: NSColor, _ width: CGFloat = 1) { color.setStroke(); let p = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius); p.lineWidth = width; p.stroke() }
func text(_ string: String, _ rect: NSRect, _ font: NSFont, _ color: NSColor, _ align: NSTextAlignment = .left) { let style = NSMutableParagraphStyle(); style.alignment = align; style.lineBreakMode = .byWordWrapping; NSAttributedString(string: string, attributes: [.font: font, .foregroundColor: color, .paragraphStyle: style]).draw(with: rect, options: [.usesLineFragmentOrigin, .usesFontLeading]) }
func line(_ a: CGPoint, _ b: CGPoint, _ color: NSColor, _ width: CGFloat = 2) { color.setStroke(); let p = NSBezierPath(); p.move(to: a); p.line(to: b); p.lineWidth = width; p.lineCapStyle = .round; p.stroke() }
func dot(_ p: CGPoint, _ radius: CGFloat, _ color: NSColor) { color.setFill(); NSBezierPath(ovalIn: NSRect(x: p.x - radius, y: p.y - radius, width: radius * 2, height: radius * 2)).fill() }

func background(_ seconds: Double) {
    ink.setFill(); NSBezierPath(rect: NSRect(origin: .zero, size: canvas)).fill()
    let shift = pulse(seconds, rate: 0.09)
    NSColor(calibratedRed: 0.045, green: 0.275, blue: 0.207, alpha: 0.62).setFill(); NSBezierPath(ovalIn: NSRect(x: -320 + shift * 130, y: 300, width: 1100, height: 1100)).fill()
    NSColor(calibratedRed: 0.085, green: 0.220, blue: 0.190, alpha: 0.52).setFill(); NSBezierPath(ovalIn: NSRect(x: 1250, y: -260 + shift * 90, width: 720, height: 720)).fill()
    for c in 0...16 { let x = CGFloat(c) * 128 + 18; line(CGPoint(x: x, y: 0), CGPoint(x: x, y: canvas.height), NSColor.white.withAlphaComponent(0.035)) }
    for r in 0...9 { let y = CGFloat(r) * 120 + 14; line(CGPoint(x: 0, y: y), CGPoint(x: canvas.width, y: y), NSColor.white.withAlphaComponent(0.028)) }
    for i in 0..<24 { let x = CGFloat((i * 263) % 1880) + 20 + CGFloat(sin(seconds * 0.48 + Double(i))) * 12; let y = CGFloat((i * 149) % 1020) + 30; dot(CGPoint(x: x, y: y), i % 4 == 0 ? 3 : 1.5, mint.withAlphaComponent(i % 4 == 0 ? 0.22 : 0.10)) }
}

func brand() {
    round(NSRect(x: 92, y: 937, width: 66, height: 66), 20, sand); text("VC", NSRect(x: 105, y: 953, width: 40, height: 29), .systemFont(ofSize: 21, weight: .bold), forest, .center)
    text("VICE CEO", NSRect(x: 177, y: 964, width: 230, height: 26), .systemFont(ofSize: 18, weight: .bold), .white)
    text("PROOF-CARRYING BUSINESS AUTONOMY", NSRect(x: 177, y: 940, width: 380, height: 20), .systemFont(ofSize: 11, weight: .semibold), mint.withAlphaComponent(0.78))
}

func title(_ scene: Scene, _ progress: CGFloat) {
    let x = 94 + (1 - ease(min(progress * 3, 1))) * -36
    text(scene.eyebrow, NSRect(x: x, y: 148, width: 800, height: 22), .systemFont(ofSize: 13, weight: .bold), mint.withAlphaComponent(0.9))
    text(scene.headline, NSRect(x: x, y: 80, width: 1040, height: 72), .systemFont(ofSize: 46, weight: .bold), .white)
}

func browser(_ image: NSImage, _ progress: CGFloat, _ badge: String) {
    let zoom = 1 + progress * 0.022
    let base = NSRect(x: 200, y: 243, width: 1520, height: 620)
    let frame = NSRect(x: base.midX - base.width * zoom / 2, y: base.midY - base.height * zoom / 2 + sin(progress * .pi) * 8, width: base.width * zoom, height: base.height * zoom)
    round(frame.insetBy(dx: -16, dy: -16), 32, NSColor.black.withAlphaComponent(0.28)); round(frame, 26, sand)
    let chrome = NSRect(x: frame.minX, y: frame.maxY - 46, width: frame.width, height: 46); round(chrome, 26, NSColor(calibratedWhite: 0.97, alpha: 1)); NSColor(calibratedWhite: 0.97, alpha: 1).setFill(); NSBezierPath(rect: NSRect(x: frame.minX, y: frame.maxY - 26, width: frame.width, height: 26)).fill()
    for i in 0..<3 { dot(CGPoint(x: frame.minX + 28 + CGFloat(i) * 18, y: frame.maxY - 23), 4.5, [coral, sand, moss][i]) }
    round(NSRect(x: frame.minX + 112, y: frame.maxY - 34, width: 420, height: 18), 9, NSColor(calibratedWhite: 0.88, alpha: 1))
    let imageFrame = NSRect(x: frame.minX + 2, y: frame.minY + 2, width: frame.width - 4, height: frame.height - 46)
    NSGraphicsContext.current?.cgContext.saveGState(); NSGraphicsContext.current?.cgContext.addPath(CGPath(roundedRect: imageFrame, cornerWidth: 19, cornerHeight: 19, transform: nil)); NSGraphicsContext.current?.cgContext.clip()
    let scale = max(imageFrame.width / image.size.width, imageFrame.height / image.size.height); image.draw(in: NSRect(x: imageFrame.midX - image.size.width * scale / 2, y: imageFrame.midY - image.size.height * scale / 2, width: image.size.width * scale, height: image.size.height * scale), from: .zero, operation: .sourceOver, fraction: 1); NSGraphicsContext.current?.cgContext.restoreGState()
    outline(frame, 26, NSColor.white.withAlphaComponent(0.42)); round(NSRect(x: frame.maxX - 242, y: frame.minY + 28, width: 206, height: 38), 19, ink.withAlphaComponent(0.88)); dot(CGPoint(x: frame.maxX - 216, y: frame.minY + 47), 5, mint); text(badge, NSRect(x: frame.maxX - 202, y: frame.minY + 38, width: 148, height: 18), .systemFont(ofSize: 12, weight: .bold), .white)
}

func node(_ p: CGPoint, _ title: String, _ detail: String, _ active: Bool, _ scale: CGFloat = 1) {
    let r: CGFloat = 64 * scale; if active { dot(p, r + 24, mint.withAlphaComponent(0.08)) }; dot(p, r, active ? moss : forest); outline(NSRect(x: p.x - r, y: p.y - r, width: r * 2, height: r * 2), r, mint.withAlphaComponent(active ? 0.78 : 0.30), active ? 2 : 1)
    text(title, NSRect(x: p.x - 58, y: p.y - 2, width: 116, height: 20), .systemFont(ofSize: 12, weight: .bold), .white, .center); text(detail, NSRect(x: p.x - 78, y: p.y - 25, width: 156, height: 18), .systemFont(ofSize: 10, weight: .regular), sand.withAlphaComponent(0.84), .center)
}

func visual(_ motif: Motif, _ progress: CGFloat, _ seconds: Double) {
    let y: CGFloat = 575
    switch motif {
    case .signals:
        let items = [("INBOX", "needs reply"), ("REGISTRY", "changed"), ("LEAD", "follow-up")]
        for (i, item) in items.enumerated() { let p = ease(max(min(progress * 3 - CGFloat(i) * 0.22, 1), 0)); let card = NSRect(x: CGFloat(315 + i * 270), y: y + (1 - p) * -70, width: 220, height: 142); round(card, 22, NSColor.white.withAlphaComponent(0.08)); outline(card, 22, mint.withAlphaComponent(0.18)); round(NSRect(x: card.minX + 20, y: card.maxY - 46, width: 40, height: 14), 7, mint.withAlphaComponent(0.74)); text(item.0, NSRect(x: card.minX + 20, y: card.minY + 70, width: 176, height: 22), .systemFont(ofSize: 13, weight: .bold), .white); text(item.1, NSRect(x: card.minX + 20, y: card.minY + 43, width: 176, height: 20), .systemFont(ofSize: 12, weight: .regular), sand.withAlphaComponent(0.76)) }
        let target: CGFloat = 1320; for i in 0..<3 { let start = CGFloat(535 + i * 270); let travel = min(max((progress - 0.32) * 2.2, 0), 1); line(CGPoint(x: start, y: y + 71), CGPoint(x: target - 78, y: y + 71), mint.withAlphaComponent(0.25)); dot(CGPoint(x: start + (target - 78 - start) * travel, y: y + 71), 7, mint) }; node(CGPoint(x: target, y: y + 71), "VICE CEO", "sorts the work", true, 1.14)
        let outcome = NSRect(x: 1502, y: y + 14, width: 240, height: 114); round(outcome, 22, sand); text("NEXT STEP", NSRect(x: outcome.minX + 24, y: outcome.maxY - 43, width: 170, height: 18), .systemFont(ofSize: 12, weight: .bold), forest); text("ready for you", NSRect(x: outcome.minX + 24, y: outcome.minY + 32, width: 180, height: 20), .systemFont(ofSize: 14, weight: .semibold), ink)
    case .agents:
        let c = [CGPoint(x: 485, y: 610), CGPoint(x: 890, y: 710), CGPoint(x: 1295, y: 610)]; for i in 0..<2 { line(c[i], c[i + 1], mint.withAlphaComponent(0.34), 3) }; node(c[0], "INSPECT", "approved sources", progress > 0.06); node(c[1], "APPLY", "business policy", progress > 0.26); node(c[2], "ROUTE", "act or escalate", progress > 0.46); let travel = min(max((progress - 0.1) * 1.85, 0), 1); dot(CGPoint(x: c[0].x + (c[1].x - c[0].x) * min(travel * 2, 1), y: c[0].y + (c[1].y - c[0].y) * min(travel * 2, 1)), 11, sand); if travel > 0.5 { let p = (travel - 0.5) * 2; dot(CGPoint(x: c[1].x + (c[2].x - c[1].x) * p, y: c[1].y + (c[2].y - c[1].y) * p), 11, sand) }
    case .outreach:
        let cards = [("CUSTOMER", "policy-backed reply"), ("OUTREACH", "consent checked"), ("FOLLOW-UP", "duplicate blocked")]; for (i, card) in cards.enumerated() { let lift = ease(max(min(progress * 2.8 - CGFloat(i) * 0.22, 1), 0)); let r = NSRect(x: CGFloat(248 + i * 480), y: 500 + lift * 60, width: 390, height: 190); round(r, 26, NSColor.white.withAlphaComponent(0.085)); outline(r, 26, mint.withAlphaComponent(0.22)); round(NSRect(x: r.minX + 26, y: r.maxY - 54, width: 52, height: 22), 11, mint.withAlphaComponent(0.80)); text(card.0, NSRect(x: r.minX + 26, y: r.minY + 106, width: 315, height: 24), .systemFont(ofSize: 15, weight: .bold), .white); text(card.1, NSRect(x: r.minX + 26, y: r.minY + 75, width: 310, height: 20), .systemFont(ofSize: 13, weight: .regular), sand.withAlphaComponent(0.82)); round(NSRect(x: r.minX + 26, y: r.minY + 29, width: 134, height: 26), 13, forest); text("READY", NSRect(x: r.minX + 53, y: r.minY + 35, width: 74, height: 14), .systemFont(ofSize: 10, weight: .bold), mint, .center) }
    case .escalation:
        let left = NSRect(x: 245, y: 484, width: 625, height: 244); round(left, 28, NSColor.white.withAlphaComponent(0.075)); outline(left, 28, coral.withAlphaComponent(0.55), 2); text("SENSITIVE REQUEST", NSRect(x: left.minX + 36, y: left.maxY - 62, width: 400, height: 22), .systemFont(ofSize: 14, weight: .bold), coral); text("Refund · legal · judgment", NSRect(x: left.minX + 36, y: left.minY + 112, width: 440, height: 28), .systemFont(ofSize: 22, weight: .bold), .white); text("Not auto-sent", NSRect(x: left.minX + 36, y: left.minY + 74, width: 260, height: 22), .systemFont(ofSize: 14, weight: .regular), sand.withAlphaComponent(0.76))
        let owner = NSRect(x: 1080, y: 484, width: 590, height: 244); round(owner, 28, sand); text("OWNER", NSRect(x: owner.minX + 36, y: owner.maxY - 62, width: 250, height: 22), .systemFont(ofSize: 14, weight: .bold), forest); text("Context, evidence,\nand a clear decision.", NSRect(x: owner.minX + 36, y: owner.minY + 91, width: 440, height: 76), .systemFont(ofSize: 24, weight: .bold), ink); let a = CGPoint(x: left.maxX + 42, y: 606); let b = CGPoint(x: owner.minX - 42, y: 606); line(a, b, mint.withAlphaComponent(0.62), 4); dot(CGPoint(x: a.x + (b.x - a.x) * min(progress * 1.6, 1), y: 606), 13, mint)
    case .receipt:
        let r = NSRect(x: 638, y: 382, width: 644, height: 390); round(r, 34, sand); text("ACTION RECEIPT", NSRect(x: r.minX + 46, y: r.maxY - 64, width: 340, height: 26), .systemFont(ofSize: 17, weight: .bold), forest); let rows = [("01", "TRIGGER", "Registry updated"), ("02", "EVIDENCE", "Source preserved"), ("03", "POLICY", "Authority checked"), ("04", "RESULT", "Next step prepared")]; for (i, row) in rows.enumerated() { let y = r.maxY - 122 - CGFloat(i) * 61; text(row.0, NSRect(x: r.minX + 46, y: y, width: 40, height: 18), .monospacedDigitSystemFont(ofSize: 12, weight: .bold), moss); text(row.1, NSRect(x: r.minX + 106, y: y, width: 108, height: 18), .systemFont(ofSize: 11, weight: .bold), forest); text(row.2, NSRect(x: r.minX + 258, y: y, width: 294, height: 18), .systemFont(ofSize: 13, weight: .semibold), ink); if i < rows.count - 1 { line(CGPoint(x: r.minX + 46, y: y - 14), CGPoint(x: r.maxX - 46, y: y - 14), forest.withAlphaComponent(0.16)) } }; let s = 0.92 + pulse(seconds, rate: 0.32) * 0.08; let stamp = NSRect(x: 1303, y: 433, width: 210 * s, height: 74 * s); round(stamp, 16, mint); text("RECORDED", stamp.insetBy(dx: 16, dy: 25), .systemFont(ofSize: 15, weight: .bold), forest, .center)
    case .cloud:
        let items = [("CLOUD RUN", CGPoint(x: 340, y: 640)), ("SCHEDULER", CGPoint(x: 700, y: 740)), ("FIRESTORE", CGPoint(x: 1080, y: 640)), ("GEMINI + ADK", CGPoint(x: 1450, y: 740))]; for (i, item) in items.enumerated() { let active = max(min(progress * 2.3 - CGFloat(i) * 0.14, 1), 0); if i > 0 { line(items[i - 1].1, item.1, mint.withAlphaComponent(0.26), 3) }; node(item.1, item.0, i == 3 ? "reasoning" : "durable work", active > 0.15, 0.88 + active * 0.12) }
    case .closing:
        let c = CGPoint(x: 960, y: 570); for i in 0..<4 { let r = CGFloat(130 + i * 82) + pulse(seconds, rate: 0.16) * 14; outline(NSRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2), r, mint.withAlphaComponent(i == 0 ? 0.38 : 0.10), i == 0 ? 3 : 1) }; round(NSRect(x: 817, y: 428, width: 286, height: 286), 74, sand); text("VC", NSRect(x: 864, y: 515, width: 190, height: 91), .systemFont(ofSize: 72, weight: .bold), forest, .center); for chip in [("EVIDENCE", CGPoint(x: 510, y: 600)), ("POLICY", CGPoint(x: 1320, y: 600)), ("ACTION", CGPoint(x: 960, y: 298))] { round(NSRect(x: chip.1.x - 72, y: chip.1.y - 18, width: 144, height: 36), 18, forest); text(chip.0, NSRect(x: chip.1.x - 54, y: chip.1.y - 6, width: 108, height: 15), .systemFont(ofSize: 10, weight: .bold), mint, .center) }
    }
}

func draw(_ scene: Scene, _ progress: CGFloat, _ seconds: Double, _ buffer: CVPixelBuffer) {
    CVPixelBufferLockBaseAddress(buffer, []); defer { CVPixelBufferUnlockBaseAddress(buffer, []) }; guard let base = CVPixelBufferGetBaseAddress(buffer) else { return }; guard let context = CGContext(data: base, width: Int(canvas.width), height: Int(canvas.height), bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue) else { return }
    let graphics = NSGraphicsContext(cgContext: context, flipped: false); NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = graphics; defer { NSGraphicsContext.restoreGraphicsState() }; background(seconds); brand()
    if let path = scene.imagePath, let image = NSImage(contentsOfFile: path) {
        let badge: String
        switch scene.motif {
        case .receipt: badge = "TRACEABLE"
        case .cloud: badge = "GOOGLE CLOUD"
        case .escalation: badge = "HUMAN REVIEW"
        case .outreach: badge = "READY TO ACT"
        default: badge = "SOURCE-LINKED"
        }
        browser(image, progress, badge)
    } else {
        visual(scene.motif, progress, seconds)
    }
    title(scene, progress)
}

func render() throws {
    try FileManager.default.createDirectory(at: artifacts, withIntermediateDirectories: true); if FileManager.default.fileExists(atPath: silentURL.path) { try FileManager.default.removeItem(at: silentURL) }; if FileManager.default.fileExists(atPath: outputURL.path) { try FileManager.default.removeItem(at: outputURL) }
    let writer = try AVAssetWriter(outputURL: silentURL, fileType: .mp4); let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: canvas.width, AVVideoHeightKey: canvas.height, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 8_000_000]]); input.expectsMediaDataInRealTime = false; let adapter = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: canvas.width, kCVPixelBufferHeightKey as String: canvas.height, kCVPixelBufferCGImageCompatibilityKey as String: true, kCVPixelBufferCGBitmapContextCompatibilityKey as String: true]); guard writer.canAdd(input) else { throw NSError(domain: "ViceCEO", code: 1) }; writer.add(input); writer.startWriting(); writer.startSession(atSourceTime: .zero)
    let total = scenes.reduce(0) { $0 + $1.weight }; let runtime = duration(); var frame: Int64 = 0
    for scene in scenes { let count = Int((runtime * scene.weight / total * Double(fps)).rounded()); for i in 0..<count { while !input.isReadyForMoreMediaData { usleep(1_000) }; guard let pool = adapter.pixelBufferPool else { throw NSError(domain: "ViceCEO", code: 2) }; var buffer: CVPixelBuffer?; CVPixelBufferPoolCreatePixelBuffer(nil, pool, &buffer); guard let buffer else { throw NSError(domain: "ViceCEO", code: 3) }; draw(scene, CGFloat(i) / CGFloat(max(count - 1, 1)), Double(frame) / Double(fps), buffer); guard adapter.append(buffer, withPresentationTime: CMTime(value: frame, timescale: fps)) else { throw writer.error ?? NSError(domain: "ViceCEO", code: 4) }; frame += 1 } }
    input.markAsFinished(); let done = DispatchSemaphore(value: 0); writer.finishWriting { done.signal() }; done.wait(); guard writer.status == .completed else { throw writer.error ?? NSError(domain: "ViceCEO", code: 5) }
}

func narrate() throws {
    guard FileManager.default.fileExists(atPath: narrationURL.path) else { try FileManager.default.copyItem(at: silentURL, to: outputURL); return }; let video = AVURLAsset(url: silentURL); let audio = AVURLAsset(url: narrationURL); let mix = AVMutableComposition(); guard let v = video.tracks(withMediaType: .video).first, let a = audio.tracks(withMediaType: .audio).first, let dv = mix.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid), let da = mix.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else { throw NSError(domain: "ViceCEO", code: 6) }; try dv.insertTimeRange(CMTimeRange(start: .zero, duration: video.duration), of: v, at: .zero); try da.insertTimeRange(CMTimeRange(start: .zero, duration: min(audio.duration, video.duration)), of: a, at: .zero); guard let export = AVAssetExportSession(asset: mix, presetName: AVAssetExportPresetHighestQuality) else { throw NSError(domain: "ViceCEO", code: 7) }; export.outputURL = outputURL; export.outputFileType = .mp4; let done = DispatchSemaphore(value: 0); export.exportAsynchronously { done.signal() }; done.wait(); guard export.status == .completed else { throw export.error ?? NSError(domain: "ViceCEO", code: 8) }
}

do { try render(); try narrate(); print("Rendered \(outputURL.path)") } catch { fputs("Video render failed: \(error)\n", stderr); exit(1) }
