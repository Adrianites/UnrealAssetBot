use pyo3::prelude::*;
use std::process::Command;

#[pyfunction]
fn download_youtube_video(url: &str, format: &str, output_path: &str) -> PyResult<()> {
    let format_option = if format == "mp4" {
        "bestvideo[height<=1080]+bestaudio/best"
    } else {
        "bestaudio/best"
    };

    let status = Command::new("yt-dlp")
        .arg("-f")
        .arg(format_option)
        .arg("-o")
        .arg(output_path)
        .arg(url)
        .status()
        .expect("Failed to execute yt-dlp");

    if status.success() {
        Ok(())
    } else {
        Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to download video"))
    }
}

#[pymodule]
fn youtube_downloader(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(download_youtube_video, m)?)?;
    Ok(())
}