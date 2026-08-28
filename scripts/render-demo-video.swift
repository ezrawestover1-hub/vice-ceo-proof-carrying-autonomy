import AppKit
import AVFoundation
import CoreVideo
import Darwin
import Foundation

struct Scene {
    let imagePath: String?
    let title: String
    let subtitle: String
    let duration: Double
}

let repository = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let artifacts = repository.appendingPathComponent("artifacts/demo-video")
let captures = artifacts.appendingPathComponent("captures")
let outputURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-Demo.mp4")
let silentURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-silent.mp4")
let narrationURL = artifacts.appendingPathComponent("vice-ceo-demo-narration.aiff")

let scenes = [
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-home.png").path,
        title: "Vice CEO — Proof-Carrying Business Autonomy",
        subtitle: "Turn any important business signal into evidence, a bounded decision, and a replayable trail.",
        duration: 32
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-evidence.png").path,
        title: "A reusable business operating pattern",
        subtitle: "Signal → evidence → specialist advice → scoped warrant → accountable decision.",
        duration: 43
    ),
    Scene(
        imagePath: nil,
        title: "First live deployment: Westover EPR",
        subtitle: "Registry Change Watch on Cloud Run • three OIDC Scheduler jobs • Firestore evidence state • one practical proof of the platform.",
        duration: 45
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-boundaries.png").path,
        title: "Useful across business workflows",
        subtitle: "Compliance, operations, support, and procurement can share the same evidence, review, and authority model.",
        duration: 48
    ),
    Scene(
        imagePath: repository.appendingPathComponent("ARCHITECTURE.png").path,
        title: "A disciplined agent architecture",
        subtitle: "Gemini 3.5 Flash + Google ADK • Cloud Run • Cloud Scheduler • Firestore • evidence-linked owner review",
        duration: 48
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-home.png").path,
        title: "Business autonomy you can inspect",
        subtitle: "Vice CEO acts in the background and earns attention only when the evidence warrants a decision.",
        duration: 34
    )
]

let canvas = CGSize(width: 1920, height: 1080)
let framesPerSecond: Int32 = 30

func drawWrapped(_ text: String, in rect: NSRect, font: NSFont, color: NSColor, alignment: NSTextAlignment = .left) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = alignment
    paragraph.lineBreakMode = .byWordWrapping
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: color,
        .paragraphStyle: paragraph
    ]
    NSAttributedString(string: text, attributes: attributes).draw(with: rect, options: [.usesLineFragmentOrigin, .usesFontLeading])
}

func drawScene(_ scene: Scene, at progress: CGFloat, in pixelBuffer: CVPixelBuffer) {
    CVPixelBufferLockBaseAddress(pixelBuffer, [])
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, []) }

    guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else { return }
    let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)
    guard let context = CGContext(
        data: baseAddress,
        width: Int(canvas.width),
        height: Int(canvas.height),
        bitsPerComponent: 8,
        bytesPerRow: bytesPerRow,
        space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
    ) else { return }

    context.setFillColor(NSColor(calibratedRed: 0.035, green: 0.075, blue: 0.067, alpha: 1).cgColor)
    context.fill(CGRect(origin: .zero, size: canvas))

    let graphicsContext = NSGraphicsContext(cgContext: context, flipped: false)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = graphicsContext
    defer { NSGraphicsContext.restoreGraphicsState() }

    if let imagePath = scene.imagePath, let image = NSImage(contentsOfFile: imagePath) {
        let sourceSize = image.size
        let scale = max(canvas.width / sourceSize.width, canvas.height / sourceSize.height)
        let zoom = 1 + (progress * 0.035)
        let rendered = CGSize(width: sourceSize.width * scale * zoom, height: sourceSize.height * scale * zoom)
        let frame = NSRect(
            x: (canvas.width - rendered.width) / 2,
            y: (canvas.height - rendered.height) / 2,
            width: rendered.width,
            height: rendered.height
        )
        image.draw(in: frame, from: .zero, operation: .sourceOver, fraction: 1)
        NSColor.black.withAlphaComponent(0.36).setFill()
        NSBezierPath(rect: NSRect(origin: .zero, size: canvas)).fill()
    } else {
        let accent = NSColor(calibratedRed: 0.14, green: 0.38, blue: 0.32, alpha: 1)
        accent.setFill()
        NSBezierPath(roundedRect: NSRect(x: 145, y: 280, width: 18, height: 500), xRadius: 9, yRadius: 9).fill()
        drawWrapped("LIVE", in: NSRect(x: 205, y: 745, width: 1300, height: 60), font: .systemFont(ofSize: 28, weight: .semibold), color: NSColor(calibratedRed: 0.48, green: 0.82, blue: 0.70, alpha: 1))
    }

    let plate = NSRect(x: 110, y: 72, width: 1700, height: 226)
    NSColor.black.withAlphaComponent(0.73).setFill()
    NSBezierPath(roundedRect: plate, xRadius: 18, yRadius: 18).fill()
    drawWrapped(scene.title, in: NSRect(x: 155, y: 205, width: 1600, height: 72), font: .systemFont(ofSize: 45, weight: .bold), color: .white)
    drawWrapped(scene.subtitle, in: NSRect(x: 155, y: 102, width: 1600, height: 86), font: .systemFont(ofSize: 26, weight: .regular), color: NSColor(white: 0.9, alpha: 1))
}

func makeVideo() throws {
    try FileManager.default.createDirectory(at: artifacts, withIntermediateDirectories: true)
    if FileManager.default.fileExists(atPath: silentURL.path) {
        try FileManager.default.removeItem(at: silentURL)
    }
    if FileManager.default.fileExists(atPath: outputURL.path) {
        try FileManager.default.removeItem(at: outputURL)
    }

    let writer = try AVAssetWriter(outputURL: silentURL, fileType: .mp4)
    let settings: [String: Any] = [
        AVVideoCodecKey: AVVideoCodecType.h264,
        AVVideoWidthKey: canvas.width,
        AVVideoHeightKey: canvas.height,
        AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 5_500_000]
    ]
    let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
    input.expectsMediaDataInRealTime = false
    let attributes: [String: Any] = [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
        kCVPixelBufferWidthKey as String: canvas.width,
        kCVPixelBufferHeightKey as String: canvas.height,
        kCVPixelBufferCGImageCompatibilityKey as String: true,
        kCVPixelBufferCGBitmapContextCompatibilityKey as String: true
    ]
    let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attributes)
    guard writer.canAdd(input) else { throw NSError(domain: "ViceCEOVideo", code: 1) }
    writer.add(input)
    writer.startWriting()
    writer.startSession(atSourceTime: .zero)

    var frameNumber: Int64 = 0
    for scene in scenes {
        let frameCount = Int((scene.duration * Double(framesPerSecond)).rounded())
        for index in 0..<frameCount {
            while !input.isReadyForMoreMediaData { usleep(1_000) }
            guard let pool = adaptor.pixelBufferPool else { throw NSError(domain: "ViceCEOVideo", code: 2) }
            var pixelBuffer: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, pool, &pixelBuffer)
            guard let pixelBuffer else { throw NSError(domain: "ViceCEOVideo", code: 3) }
            drawScene(scene, at: CGFloat(index) / CGFloat(max(frameCount - 1, 1)), in: pixelBuffer)
            let presentationTime = CMTime(value: frameNumber, timescale: framesPerSecond)
            guard adaptor.append(pixelBuffer, withPresentationTime: presentationTime) else {
                throw writer.error ?? NSError(domain: "ViceCEOVideo", code: 4)
            }
            frameNumber += 1
        }
    }
    input.markAsFinished()
    let completion = DispatchSemaphore(value: 0)
    writer.finishWriting { completion.signal() }
    completion.wait()
    guard writer.status == .completed else { throw writer.error ?? NSError(domain: "ViceCEOVideo", code: 5) }
}

func addNarration() throws {
    guard FileManager.default.fileExists(atPath: narrationURL.path) else {
        try FileManager.default.copyItem(at: silentURL, to: outputURL)
        return
    }
    let video = AVURLAsset(url: silentURL)
    let audio = AVURLAsset(url: narrationURL)
    let composition = AVMutableComposition()
    guard let sourceVideo = video.tracks(withMediaType: .video).first,
          let sourceAudio = audio.tracks(withMediaType: .audio).first,
          let destinationVideo = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid) else {
        throw NSError(domain: "ViceCEOVideo", code: 6)
    }

    try destinationVideo.insertTimeRange(CMTimeRange(start: .zero, duration: video.duration), of: sourceVideo, at: .zero)
    guard let destinationAudio = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else {
        throw NSError(domain: "ViceCEOVideo", code: 7)
    }
    let audioDuration = min(audio.duration, video.duration)
    try destinationAudio.insertTimeRange(CMTimeRange(start: .zero, duration: audioDuration), of: sourceAudio, at: .zero)

    guard let export = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else {
        throw NSError(domain: "ViceCEOVideo", code: 8)
    }
    export.outputURL = outputURL
    export.outputFileType = .mp4
    let completion = DispatchSemaphore(value: 0)
    export.exportAsynchronously { completion.signal() }
    completion.wait()
    guard export.status == .completed else { throw export.error ?? NSError(domain: "ViceCEOVideo", code: 9) }
}

do {
    try makeVideo()
    try addNarration()
    print("Rendered \(outputURL.path)")
} catch {
    fputs("Video render failed: \(error)\n", stderr)
    exit(1)
}
