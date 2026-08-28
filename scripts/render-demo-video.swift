import AppKit
import AVFoundation
import CoreVideo
import Darwin
import Foundation

struct TourScene {
    let imagePath: String
    let label: String
    let startFocus: CGPoint
    let endFocus: CGPoint
    let startZoom: CGFloat
    let endZoom: CGFloat
    let weight: Double
}

let repository = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let artifacts = repository.appendingPathComponent("artifacts/demo-video")
let captures = artifacts.appendingPathComponent("captures")
let outputURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-Demo.mp4")
let silentURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-silent.mp4")
let narrationURL = URL(fileURLWithPath: ProcessInfo.processInfo.environment["VICE_CEO_NARRATION_PATH"] ?? artifacts.appendingPathComponent("vice-ceo-demo-narration.mp3").path)

let scenes = [
    TourScene(imagePath: captures.appendingPathComponent("live-work.png").path, label: "LIVE WORKSPACE", startFocus: CGPoint(x: 0.50, y: 0.51), endFocus: CGPoint(x: 0.30, y: 0.62), startZoom: 0.99, endZoom: 1.18, weight: 27),
    TourScene(imagePath: captures.appendingPathComponent("live-work.png").path, label: "ROUTINE CUSTOMER WORK", startFocus: CGPoint(x: 0.30, y: 0.62), endFocus: CGPoint(x: 0.57, y: 0.62), startZoom: 1.18, endZoom: 1.21, weight: 28),
    TourScene(imagePath: captures.appendingPathComponent("live-reply-receipt.png").path, label: "REPLY RECEIPT", startFocus: CGPoint(x: 0.56, y: 0.58), endFocus: CGPoint(x: 0.83, y: 0.80), startZoom: 1.03, endZoom: 1.18, weight: 24),
    TourScene(imagePath: captures.appendingPathComponent("live-work.png").path, label: "CONSENTED FOLLOW-UPS", startFocus: CGPoint(x: 0.79, y: 0.61), endFocus: CGPoint(x: 0.80, y: 0.69), startZoom: 1.15, endZoom: 1.24, weight: 26),
    TourScene(imagePath: captures.appendingPathComponent("live-follow-up-receipt.png").path, label: "FOLLOW-UP RECEIPT", startFocus: CGPoint(x: 0.80, y: 0.67), endFocus: CGPoint(x: 0.83, y: 0.82), startZoom: 1.08, endZoom: 1.20, weight: 22),
    TourScene(imagePath: captures.appendingPathComponent("live-activity.png").path, label: "EXCEPTIONS COME TO YOU", startFocus: CGPoint(x: 0.50, y: 0.67), endFocus: CGPoint(x: 0.57, y: 0.75), startZoom: 1.02, endZoom: 1.16, weight: 24),
    TourScene(imagePath: captures.appendingPathComponent("live-work.png").path, label: "DELIVERY IS YOUR CHOICE", startFocus: CGPoint(x: 0.50, y: 0.82), endFocus: CGPoint(x: 0.50, y: 0.48), startZoom: 1.13, endZoom: 1.03, weight: 27),
    TourScene(imagePath: captures.appendingPathComponent("live-work.png").path, label: "VICE CEO", startFocus: CGPoint(x: 0.50, y: 0.51), endFocus: CGPoint(x: 0.53, y: 0.52), startZoom: 1.00, endZoom: 1.07, weight: 20)
]

let canvas = CGSize(width: 1920, height: 1080)
let fps: Int32 = 30
let ink = NSColor(calibratedRed: 0.026, green: 0.060, blue: 0.050, alpha: 1)
let forest = NSColor(calibratedRed: 0.040, green: 0.310, blue: 0.230, alpha: 1)
let mint = NSColor(calibratedRed: 0.58, green: 0.93, blue: 0.78, alpha: 1)
let sand = NSColor(calibratedRed: 0.95, green: 0.91, blue: 0.81, alpha: 1)

func runtime() -> Double {
    let value = CMTimeGetSeconds(AVURLAsset(url: narrationURL).duration)
    return value.isFinite && value > 0 ? value + 0.5 : 173
}

func clamp(_ value: CGFloat) -> CGFloat { min(max(value, 0), 1) }
func ease(_ value: CGFloat) -> CGFloat { let x = clamp(value); return x * x * (3 - 2 * x) }
func mix(_ a: CGFloat, _ b: CGFloat, _ amount: CGFloat) -> CGFloat { a + (b - a) * amount }
func mix(_ a: CGPoint, _ b: CGPoint, _ amount: CGFloat) -> CGPoint { CGPoint(x: mix(a.x, b.x, amount), y: mix(a.y, b.y, amount)) }

func rounded(_ rect: NSRect, radius: CGFloat, color: NSColor) {
    color.setFill()
    NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius).fill()
}

func drawText(_ text: String, rect: NSRect, font: NSFont, color: NSColor, alignment: NSTextAlignment = .left) {
    let style = NSMutableParagraphStyle()
    style.alignment = alignment
    NSAttributedString(string: text, attributes: [.font: font, .foregroundColor: color, .paragraphStyle: style]).draw(with: rect, options: [.usesLineFragmentOrigin])
}

func dot(_ point: CGPoint, radius: CGFloat, color: NSColor) {
    color.setFill()
    NSBezierPath(ovalIn: NSRect(x: point.x - radius, y: point.y - radius, width: radius * 2, height: radius * 2)).fill()
}

func drawScreen(_ image: NSImage, scene: TourScene, progress: CGFloat) {
    let motion = ease(progress)
    let focus = mix(scene.startFocus, scene.endFocus, motion)
    let zoom = mix(scene.startZoom, scene.endZoom, motion)
    let source = image.size
    let scale = max(canvas.width / source.width, canvas.height / source.height) * zoom
    let rendered = CGSize(width: source.width * scale, height: source.height * scale)
    let desiredX = canvas.width / 2 - focus.x * rendered.width
    let desiredY = canvas.height / 2 - focus.y * rendered.height
    let frame = NSRect(
        x: min(max(desiredX, canvas.width - rendered.width), 0),
        y: min(max(desiredY, canvas.height - rendered.height), 0),
        width: rendered.width,
        height: rendered.height
    )
    image.draw(in: frame, from: .zero, operation: .sourceOver, fraction: 1)

    let edge = NSColor.black.withAlphaComponent(0.14)
    edge.setFill()
    NSBezierPath(rect: NSRect(x: 0, y: 0, width: canvas.width, height: 56)).fill()
    NSBezierPath(rect: NSRect(x: 0, y: 0, width: 38, height: canvas.height)).fill()
    NSBezierPath(rect: NSRect(x: canvas.width - 38, y: 0, width: 38, height: canvas.height)).fill()

    let marker = CGPoint(x: canvas.width / 2 + (focus.x - 0.5) * 220, y: canvas.height / 2 + (focus.y - 0.5) * 125)
    let alpha = progress < 0.82 ? 0.44 : 0.16
    dot(marker, radius: 19 + sin(Double(progress) * .pi * 4) * 2, color: mint.withAlphaComponent(alpha * 0.18))
    dot(marker, radius: 6, color: mint.withAlphaComponent(alpha))
}

func drawChrome(label: String, sceneIndex: Int, progress: CGFloat) {
    rounded(NSRect(x: 38, y: 1006, width: 325, height: 42), radius: 21, color: ink.withAlphaComponent(0.88))
    dot(CGPoint(x: 63, y: 1027), radius: 5, color: mint)
    drawText("LIVE DEMO  /  \(label)", rect: NSRect(x: 80, y: 1019, width: 256, height: 17), font: .systemFont(ofSize: 11, weight: .bold), color: .white)

    let bar = NSRect(x: 1510, y: 1022, width: 360, height: 8)
    rounded(bar, radius: 4, color: NSColor.white.withAlphaComponent(0.46))
    let overall = (CGFloat(sceneIndex) + progress) / CGFloat(scenes.count)
    rounded(NSRect(x: bar.minX, y: bar.minY, width: bar.width * overall, height: bar.height), radius: 4, color: forest)
}

func drawFrame(_ scene: TourScene, sceneIndex: Int, progress: CGFloat, pixelBuffer: CVPixelBuffer) {
    CVPixelBufferLockBaseAddress(pixelBuffer, [])
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, []) }
    guard let base = CVPixelBufferGetBaseAddress(pixelBuffer),
          let context = CGContext(data: base, width: Int(canvas.width), height: Int(canvas.height), bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pixelBuffer), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue) else { return }
    let graphics = NSGraphicsContext(cgContext: context, flipped: false)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = graphics
    defer { NSGraphicsContext.restoreGraphicsState() }
    NSColor.white.setFill()
    NSBezierPath(rect: NSRect(origin: .zero, size: canvas)).fill()
    if let image = NSImage(contentsOfFile: scene.imagePath) { drawScreen(image, scene: scene, progress: progress) }
    drawChrome(label: scene.label, sceneIndex: sceneIndex, progress: progress)
}

func makeVideo() throws {
    try FileManager.default.createDirectory(at: artifacts, withIntermediateDirectories: true)
    if FileManager.default.fileExists(atPath: silentURL.path) { try FileManager.default.removeItem(at: silentURL) }
    if FileManager.default.fileExists(atPath: outputURL.path) { try FileManager.default.removeItem(at: outputURL) }
    let writer = try AVAssetWriter(outputURL: silentURL, fileType: .mp4)
    let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: canvas.width, AVVideoHeightKey: canvas.height, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 9_000_000]])
    input.expectsMediaDataInRealTime = false
    let adapter = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: canvas.width, kCVPixelBufferHeightKey as String: canvas.height, kCVPixelBufferCGImageCompatibilityKey as String: true, kCVPixelBufferCGBitmapContextCompatibilityKey as String: true])
    guard writer.canAdd(input) else { throw NSError(domain: "ViceCEOVideo", code: 1) }
    writer.add(input)
    writer.startWriting()
    writer.startSession(atSourceTime: .zero)
    let totalWeight = scenes.reduce(0) { $0 + $1.weight }
    var frame: Int64 = 0
    for (sceneIndex, scene) in scenes.enumerated() {
        let count = Int((runtime() * scene.weight / totalWeight * Double(fps)).rounded())
        for index in 0..<count {
            while !input.isReadyForMoreMediaData { usleep(1_000) }
            guard let pool = adapter.pixelBufferPool else { throw NSError(domain: "ViceCEOVideo", code: 2) }
            var buffer: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, pool, &buffer)
            guard let buffer else { throw NSError(domain: "ViceCEOVideo", code: 3) }
            drawFrame(scene, sceneIndex: sceneIndex, progress: CGFloat(index) / CGFloat(max(count - 1, 1)), pixelBuffer: buffer)
            guard adapter.append(buffer, withPresentationTime: CMTime(value: frame, timescale: fps)) else { throw writer.error ?? NSError(domain: "ViceCEOVideo", code: 4) }
            frame += 1
        }
    }
    input.markAsFinished()
    let done = DispatchSemaphore(value: 0)
    writer.finishWriting { done.signal() }
    done.wait()
    guard writer.status == .completed else { throw writer.error ?? NSError(domain: "ViceCEOVideo", code: 5) }
}

func addNarration() throws {
    guard FileManager.default.fileExists(atPath: narrationURL.path) else { try FileManager.default.copyItem(at: silentURL, to: outputURL); return }
    let video = AVURLAsset(url: silentURL)
    let audio = AVURLAsset(url: narrationURL)
    let composition = AVMutableComposition()
    guard let sourceVideo = video.tracks(withMediaType: .video).first,
          let sourceAudio = audio.tracks(withMediaType: .audio).first,
          let destinationVideo = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid),
          let destinationAudio = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else { throw NSError(domain: "ViceCEOVideo", code: 6) }
    try destinationVideo.insertTimeRange(CMTimeRange(start: .zero, duration: video.duration), of: sourceVideo, at: .zero)
    try destinationAudio.insertTimeRange(CMTimeRange(start: .zero, duration: min(video.duration, audio.duration)), of: sourceAudio, at: .zero)
    guard let export = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else { throw NSError(domain: "ViceCEOVideo", code: 7) }
    export.outputURL = outputURL
    export.outputFileType = .mp4
    let done = DispatchSemaphore(value: 0)
    export.exportAsynchronously { done.signal() }
    done.wait()
    guard export.status == .completed else { throw export.error ?? NSError(domain: "ViceCEOVideo", code: 8) }
}

do {
    try makeVideo()
    try addNarration()
    print("Rendered \(outputURL.path)")
} catch {
    fputs("Video render failed: \(error)\n", stderr)
    exit(1)
}
