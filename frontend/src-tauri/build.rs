fn main() {
  tauri_build::build();

  // Build protobuf (optional for now)
  // tonic_build::compile_protos("proto/video_analyzer.proto")
  //     .unwrap_or_else(|e| panic!("Failed to compile protos {:?}", e));
}
