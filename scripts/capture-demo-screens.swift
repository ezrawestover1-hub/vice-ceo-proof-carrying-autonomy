import AppKit
import Foundation
import WebKit

final class DemoCapture: NSObject, WKNavigationDelegate {
    private let outputDirectory: URL
    private let webView: WKWebView
    private let window: NSWindow
    private var index = 0
    private let pages: [(name: String, action: String?)] = [
        ("live-work", nil),
        ("live-reply-receipt", "document.querySelector('[data-action=send_customer_reply]').click()"),
        ("live-follow-up-receipt", "document.querySelector('[data-action=send_outreach_follow_up]').click()"),
        ("live-activity", "document.querySelector('#activity').scrollIntoView({block: 'center'})")
    ]

    init(outputDirectory: URL) {
        self.outputDirectory = outputDirectory
        let frame = NSRect(x: 0, y: 0, width: 1728, height: 940)
        self.window = NSWindow(contentRect: frame, styleMask: [.titled], backing: .buffered, defer: false)
        self.webView = WKWebView(frame: frame)
        super.init()
        window.contentView = webView
        webView.navigationDelegate = self
        window.orderOut(nil)
    }

    func start() {
        loadCurrentPage()
    }

    private func loadCurrentPage() {
        guard index < pages.count else { NSApp.terminate(nil); return }
        let url = URL(string: "https://vice-ceo-review-demo-77u4kmu2ba-uc.a.run.app/demo")!
        webView.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData))
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        let action = pages[index].action ?? "void 0"
        webView.evaluateJavaScript(action) { [self] _, error in
            if let error {
                fputs("Could not prepare \(pages[index].name): \(error)\n", stderr)
                exit(1)
            }
            captureCurrentPage()
        }
    }

    private func captureCurrentPage() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [self] in
            let configuration = WKSnapshotConfiguration()
            configuration.rect = webView.bounds
            configuration.snapshotWidth = 1728
            webView.takeSnapshot(with: configuration) { [self] image, error in
                guard let image, error == nil,
                      let tiff = image.tiffRepresentation,
                      let bitmap = NSBitmapImageRep(data: tiff),
                      let png = bitmap.representation(using: .png, properties: [:]) else {
                    fputs("Could not capture \(pages[index].name): \(String(describing: error))\n", stderr)
                    exit(1)
                }
                let destination = outputDirectory.appendingPathComponent("\(pages[index].name).png")
                do {
                    try png.write(to: destination)
                    print("Captured \(destination.path)")
                    index += 1
                    loadCurrentPage()
                } catch {
                    fputs("Could not save snapshot: \(error)\n", stderr)
                    exit(1)
                }
            }
        }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        fputs("Could not load page: \(error)\n", stderr)
        exit(1)
    }
}

let outputDirectory = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    .appendingPathComponent("artifacts/demo-video/captures")
try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let capture = DemoCapture(outputDirectory: outputDirectory)
capture.start()
app.run()
