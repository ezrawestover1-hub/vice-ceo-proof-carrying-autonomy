import AVFoundation
import Foundation

let repository = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let artifacts = repository.appendingPathComponent("artifacts/demo-video")
let videoURL = artifacts.appendingPathComponent(ProcessInfo.processInfo.environment["VICE_CEO_VIDEO_NAME"] ?? "ViceCEO-AllThingsAgentic-Frederick-127s.mp4")
let audioURL = artifacts.appendingPathComponent(ProcessInfo.processInfo.environment["VICE_CEO_AUDIO_NAME"] ?? "ViceCEO-Frederick-127s.mp3")
let outputURL = artifacts.appendingPathComponent(ProcessInfo.processInfo.environment["VICE_CEO_MIXED_NAME"] ?? "ViceCEO-AllThingsAgentic-Frederick-Final.mp4")

guard FileManager.default.fileExists(atPath: videoURL.path),
      FileManager.default.fileExists(atPath: audioURL.path) else {
    fputs("Expected video and audio files in \(artifacts.path)\n", stderr)
    exit(1)
}

if FileManager.default.fileExists(atPath: outputURL.path) {
    try FileManager.default.removeItem(at: outputURL)
}

let videoAsset = AVURLAsset(url: videoURL)
let audioAsset = AVURLAsset(url: audioURL)
let composition = AVMutableComposition()
guard let sourceVideo = videoAsset.tracks(withMediaType: .video).first,
      let sourceAudio = audioAsset.tracks(withMediaType: .audio).first,
      let destinationVideo = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid) else {
    fputs("Could not load the narration or video track.\n", stderr)
    exit(1)
}

guard let destinationAudio = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else {
    fputs("Could not create the destination audio track.\n", stderr)
    exit(1)
}

try destinationVideo.insertTimeRange(CMTimeRange(start: .zero, duration: videoAsset.duration), of: sourceVideo, at: .zero)
try destinationAudio.insertTimeRange(CMTimeRange(start: .zero, duration: min(videoAsset.duration, audioAsset.duration)), of: sourceAudio, at: .zero)

guard let export = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else {
    fputs("Could not create the final video export.\n", stderr)
    exit(1)
}

export.outputURL = outputURL
export.outputFileType = .mp4
let finished = DispatchSemaphore(value: 0)
export.exportAsynchronously { finished.signal() }
finished.wait()

guard export.status == .completed else {
    fputs("Narration mix failed: \(String(describing: export.error))\n", stderr)
    exit(1)
}

print("Mixed narration into \(outputURL.path)")
