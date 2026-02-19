// // Prevents additional console window on Windows in release
// #![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// fn main() {
//     tauri::Builder::default()
//         .run(tauri::generate_context!())
//         .expect("error while running tauri application");
// }

// Prevents additional console window on Windows in release
// #![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// use std::process::Command;

// #[tauri::command]
// async fn analyze_video(video_path: String) -> Result<String, String> {
//     // For now, just call Python script directly
//     println!("Analyzing video: {}", video_path);
    
//     // This is a simple approach - call Python script
//     let output = Command::new("python")
//         .arg("../backend/client_test.py")
//         .arg(&video_path)
//         .output()
//         .map_err(|e| e.to_string())?;
    
//     if output.status.success() {
//         Ok(String::from_utf8_lossy(&output.stdout).to_string())
//     } else {
//         Err(String::from_utf8_lossy(&output.stderr).to_string())
//     }
// }

// fn main() {
//     tauri::Builder::default()
//         .invoke_handler(tauri::generate_handler![analyze_video])
//         .run(tauri::generate_context!())
//         .expect("error while running tauri application");
// }

// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

#[tauri::command]
async fn analyze_video_grpc(video_data: Vec<u8>, video_name: String) -> Result<String, String> {
    println!("[Tauri] Received video: {} ({} bytes)", video_name, video_data.len());
    
    // Save video to temp file
    let temp_dir = std::env::temp_dir();
    let video_path = temp_dir.join(&video_name);
    
    println!("[Tauri] Saving to: {:?}", video_path);
    
    let mut file = File::create(&video_path)
        .map_err(|e| format!("Failed to create temp file: {}", e))?;
    
    file.write_all(&video_data)
        .map_err(|e| format!("Failed to write video data: {}", e))?;
    
    println!("[Tauri] Video saved, calling Python client...");
    
    // Get the backend path (assuming it's relative to the frontend)
    let backend_path = PathBuf::from("../../backend");
    let client_script = backend_path.join("client_test.py");
    
    println!("[Tauri] Client script: {:?}", client_script);
    
    // Call Python gRPC client
    let output = Command::new("python")
        .arg(client_script)
        .arg(&video_path)
        .output()
        .map_err(|e| format!("Failed to run Python client: {}", e))?;
    
    // Clean up temp file
    let _ = std::fs::remove_file(&video_path);
    
    if output.status.success() {
        let result = String::from_utf8_lossy(&output.stdout).to_string();
        println!("[Tauri] Success! Result length: {}", result.len());
        Ok(result)
    } else {
        let error = String::from_utf8_lossy(&output.stderr).to_string();
        println!("[Tauri] Error: {}", error);
        Err(error)
    }
}

#[tauri::command]
async fn generate_report(analysis_id: String, format: String) -> Result<String, String> {
    println!("[Tauri] Generating report for: {}", analysis_id);
    
    let backend_dir = r"D:\Users\User\ProjectVSCode\video-analyzer\backend";
    let python_exe = "python";
    
    // Call Python client
    let output = Command::new(python_exe)
        .current_dir(backend_dir)
        .arg("client_test.py")
        .arg("--report")
        .arg(&analysis_id)
        .arg(&format)
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;
    
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    
    if !stderr.is_empty() {
        eprintln!("[Tauri] Python stderr: {}", stderr);
    }
    
    if output.status.success() && !stdout.is_empty() {
        Ok(stdout)
    } else {
        Err(format!("Python error: {}", stderr))
    }
}

#[tauri::command]
async fn send_chat_message(
    message: String, 
    conversation_id: String,
    _context_json: String
) -> Result<String, String> {
    println!("[Tauri] Sending chat: {}", message);
    
    let backend_dir = r"D:\Users\User\ProjectVSCode\video-analyzer\backend";
    let python_exe = "python";
    
    // Call Python client
    let output = Command::new(python_exe)
        .current_dir(backend_dir)
        .arg("client_test.py")
        .arg("--chat")
        .arg(&message)
        .arg(&conversation_id)
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;
    
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    
    if !stderr.is_empty() {
        eprintln!("[Tauri] Python stderr: {}", stderr);
    }
    
    if output.status.success() && !stdout.is_empty() {
        Ok(stdout)
    } else {
        Err(format!("Python error: {}", stderr))
    }
}

#[tauri::command]
async fn get_conversation_history(conversation_id: String) -> Result<String, String> {
    println!("[Tauri] Getting history: {}", conversation_id);
    
    let backend_dir = r"D:\Users\User\ProjectVSCode\video-analyzer\backend";
    let python_exe = "python";
    
    let output = Command::new(python_exe)
        .current_dir(backend_dir)
        .arg("client_test.py")
        .arg("--history")
        .arg(&conversation_id)
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;
    
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    
    if output.status.success() && !stdout.is_empty() {
        Ok(stdout)
    } else {
        Err("Failed to get history".to_string())
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            analyze_video_grpc,
            generate_report,
            send_chat_message,
            get_conversation_history 
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
