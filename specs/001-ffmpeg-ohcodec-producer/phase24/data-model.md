# Phase24 数据模型
- Session：caseId/sampleId、PID、instanceId、GPU/decoder期望、源/HAP/七库SHA、wallStart、monotonicStart、targetSeconds、speed、discontinuities、endReason。prepared→playing→completed/failed/cancelled；中断不能重置start伪装连续。
- Observation：monotonicSeconds、wallUTC、property、value（可null）、errorCode。time-pos为媒体进度；PTS采样计数独立于GPU presented frames。资源fd/threads/RSS不可读为null+error。
- Media：publicId、SHA或严格说明未完整hash、fileSize、duration、codec/profile、pixelFormat/transfer/primaries/matrix、sourceType。私人path仅本地配置。远端未完整读不能声称fullSHA。
- HDRResult：inputVerified、hardwareDecodeObserved、decoderAllocationVerified、rendererOutputBits、colorApiErrors、displayCapability、visualAccepted，分别为值/unknown，不合成hdrPassed。
- Verdict：evidenceComplete、continuousPlaybackPassed、reasonCodes、manualAudio/visualPending、formalArtifactAllowed=false。
- PrivateConfig：用户名/密码/domain来自外部0600文件；不打印、不记录密码摘要、不进manifest/CI。
