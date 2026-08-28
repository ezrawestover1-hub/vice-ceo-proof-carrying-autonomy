import AppKit
import AVFoundation
import CoreVideo
import Darwin
import Foundation

struct Scene {
    let imagePath: String?
    let title: String
    let subtitle: String
    let weight: Double
}

struct Caption {
    let start: Double
    let end: Double
    let text: String
}

let repository = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let artifacts = repository.appendingPathComponent("artifacts/demo-video")
let captures = artifacts.appendingPathComponent("captures")
let outputURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-Demo.mp4")
let silentURL = artifacts.appendingPathComponent("ViceCEO-AllThingsAgentic-silent.mp4")
let narrationURL = URL(fileURLWithPath: ProcessInfo.processInfo.environment[
    "VICE_CEO_NARRATION_PATH"
] ?? artifacts.appendingPathComponent("vice-ceo-demo-narration.mp3").path)

let scenes = [
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-home.png").path,
        title: "Work handled before it becomes work.",
        subtitle: "Vice CEO turns the business work that disappears into inboxes, browser tabs, and memory into a visible operating queue.",
        weight: 29
    ),
    Scene(
        imagePath: nil,
        title: "Autonomy starts before the owner looks.",
        subtitle: "The agent watches approved operational signals, decides whether a change matters, and stays quiet when nothing needs attention.",
        weight: 31
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-evidence.png").path,
        title: "From public change to a useful next step.",
        subtitle: "The Registry Change Watch preserves source evidence, explains why a material change matters, and prepares an owner briefing.",
        weight: 33
    ),
    Scene(
        imagePath: nil,
        title: "Agentic AI with jobs, limits, and proof.",
        subtitle: "Gemini and Google ADK specialists work from bounded information. Policies decide what can progress; AI does not receive unlimited authority.",
        weight: 34
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-home.png").path,
        title: "Routine customer work moves forward.",
        subtitle: "Vice CEO prepares policy-backed replies and keeps approved, consented outreach follow-ups from falling through the cracks.",
        weight: 32
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-boundaries.png").path,
        title: "Only exceptions ask for attention.",
        subtitle: "Sensitive, financial, legal, and judgment-heavy work is escalated with context. Vice CEO does not send a guess.",
        weight: 31
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-evidence.png").path,
        title: "Every action carries its evidence.",
        subtitle: "A receipt records what started the work, which policy applied, what the agent prepared, and whether a person needed to decide.",
        weight: 32
    ),
    Scene(
        imagePath: repository.appendingPathComponent("ARCHITECTURE.png").path,
        title: "Built for background business work.",
        subtitle: "Cloud Run, Scheduler, Firestore, Gemini, and ADK support durable asynchronous work while public review stays synthetic and safe.",
        weight: 34
    ),
    Scene(
        imagePath: captures.appendingPathComponent("reviewer-home.png").path,
        title: "See what it already handled.",
        subtitle: "Vice CEO takes care of repeatable work, so business owners can focus on decisions only they can make.",
        weight: 29
    )
]

let canvas = CGSize(width: 1920, height: 1080)
let framesPerSecond: Int32 = 30

// Timed to the finalized 2:52 ElevenLabs take. Captions are intentionally
// short so they remain readable while the reviewer watches the product.
let captions = [
    Caption(start: 0.0, end: 5.6, text: "Businesses do not fall behind because owners are not working hard."),
    Caption(start: 5.6, end: 10.2, text: "They fall behind because small, important work never stops."),
    Caption(start: 10.2, end: 17.0, text: "A customer needs an answer. A lead needs a follow-up. A policy changes."),
    Caption(start: 17.0, end: 24.6, text: "Something important gets buried in an inbox until it becomes urgent."),
    Caption(start: 24.6, end: 30.8, text: "Vice CEO is not another chatbot waiting for instructions."),
    Caption(start: 30.8, end: 36.5, text: "It is a behind-the-scenes business operator that works while you work."),
    Caption(start: 36.5, end: 42.0, text: "Westover EPR is the first real-world example."),
    Caption(start: 42.0, end: 48.4, text: "Vice CEO watches approved public EPR registries in the background."),
    Caption(start: 48.4, end: 53.8, text: "It compares what is there now with what it saw before."),
    Caption(start: 53.8, end: 59.1, text: "If nothing meaningful changed, it stays quiet."),
    Caption(start: 59.1, end: 67.7, text: "When something changes, Vice CEO preserves evidence and prepares a clear next step."),
    Caption(start: 67.7, end: 73.7, text: "It does not just create another alert."),
    Caption(start: 73.7, end: 79.8, text: "It turns changing public information into organized follow-through."),
    Caption(start: 79.8, end: 84.8, text: "This is what makes Vice CEO agentic."),
    Caption(start: 84.8, end: 93.4, text: "Gemini and Google ADK work as specialized agents with clear jobs and limits."),
    Caption(start: 93.4, end: 101.0, text: "One inspects approved information. Another applies policy. Another routes the work."),
    Caption(start: 101.0, end: 106.5, text: "AI turns evidence into a useful action."),
    Caption(start: 106.5, end: 114.4, text: "But it never receives unlimited authority."),
    Caption(start: 114.4, end: 122.3, text: "It cannot invent decisions or send messages without the business enabling that authority."),
    Caption(start: 122.3, end: 127.4, text: "Every important step is recorded, explainable, and reviewable."),
    Caption(start: 127.4, end: 134.0, text: "Vice CEO handles the work that falls through the cracks every day."),
    Caption(start: 134.0, end: 141.4, text: "It prepares routine customer responses using approved policy and the original message."),
    Caption(start: 141.4, end: 149.2, text: "It keeps consented outreach ready, blocks duplicates, and stops on reply or unsubscribe."),
    Caption(start: 149.2, end: 157.2, text: "When enabled, it can send approved low-risk work through the company mailbox."),
    Caption(start: 157.2, end: 162.0, text: "Until then, it prepares the work so the business stays in control."),
    Caption(start: 162.0, end: 166.2, text: "Good autonomy is not doing everything automatically."),
    Caption(start: 166.2, end: 170.4, text: "Sensitive work needs judgment. Vice CEO brings the owner the context."),
    Caption(start: 170.4, end: 172.1, text: "You open Vice CEO to see what it already handled.")
]

func plannedVideoDuration() -> Double {
    guard FileManager.default.fileExists(atPath: narrationURL.path) else { return 250 }
    let audio = AVURLAsset(url: narrationURL)
    let seconds = CMTimeGetSeconds(audio.duration)
    guard seconds.isFinite, seconds > 0 else { return 250 }
    // Keep the full narration and leave a short final frame for the closing line.
    return seconds + 0.5
}

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

func caption(at seconds: Double) -> String? {
    captions.first(where: { seconds >= $0.start && seconds < $0.end })?.text
}

func drawScene(_ scene: Scene, at progress: CGFloat, timelineSeconds: Double, in pixelBuffer: CVPixelBuffer) {
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

    let plate = NSRect(x: 110, y: 818, width: 1700, height: 178)
    NSColor.black.withAlphaComponent(0.73).setFill()
    NSBezierPath(roundedRect: plate, xRadius: 18, yRadius: 18).fill()
    drawWrapped(scene.title, in: NSRect(x: 155, y: 914, width: 1600, height: 58), font: .systemFont(ofSize: 43, weight: .bold), color: .white)
    drawWrapped(scene.subtitle, in: NSRect(x: 155, y: 845, width: 1600, height: 62), font: .systemFont(ofSize: 24, weight: .regular), color: NSColor(white: 0.9, alpha: 1))

    if let text = caption(at: timelineSeconds) {
        let captionPlate = NSRect(x: 202, y: 76, width: 1516, height: 132)
        NSColor.black.withAlphaComponent(0.86).setFill()
        NSBezierPath(roundedRect: captionPlate, xRadius: 22, yRadius: 22).fill()
        drawWrapped(
            text,
            in: NSRect(x: 250, y: 105, width: 1420, height: 76),
            font: .systemFont(ofSize: 34, weight: .semibold),
            color: .white,
            alignment: .center
        )
    }
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

    let totalWeight = scenes.reduce(0) { $0 + $1.weight }
    let timelineDuration = plannedVideoDuration()
    var frameNumber: Int64 = 0
    for scene in scenes {
        let frameCount = Int((timelineDuration * scene.weight / totalWeight * Double(framesPerSecond)).rounded())
        for index in 0..<frameCount {
            while !input.isReadyForMoreMediaData { usleep(1_000) }
            guard let pool = adaptor.pixelBufferPool else { throw NSError(domain: "ViceCEOVideo", code: 2) }
            var pixelBuffer: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, pool, &pixelBuffer)
            guard let pixelBuffer else { throw NSError(domain: "ViceCEOVideo", code: 3) }
            let timelineSeconds = Double(frameNumber) / Double(framesPerSecond)
            drawScene(
                scene,
                at: CGFloat(index) / CGFloat(max(frameCount - 1, 1)),
                timelineSeconds: timelineSeconds,
                in: pixelBuffer
            )
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
