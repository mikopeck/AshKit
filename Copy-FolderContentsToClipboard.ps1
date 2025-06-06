#Requires -Version 3.0
<#
.SYNOPSIS
    Copies the content of all text-based files tracked by Git in the current repository to the clipboard.
    It prepends each file's content with its relative path (from repo root) for context.
    Excludes itself and files within a 'data' folder.

.DESCRIPTION
    This script first checks if the current directory is the root of a Git repository.
    If it is, it uses "git ls-files" to get a list of all files tracked by Git.
    It then filters out the script file itself and any files located within a 'data' directory
    at the repository root.
    For each remaining tracked file, it attempts to identify it as a text file based on the $TextFileExtensions list.
    For identified text files, it reads their content and adds a header line indicating the file's path.
    All content is then combined into a single string and copied to the clipboard.

.NOTES
    Author: Your AI Assistant
    Version: 1.4
    Requires Git to be installed and accessible in the system's PATH.
    Be cautious when running this in repositories with very large files,
    as it might consume a lot of memory and take time.
    Binary files tracked by Git might produce garbled text if not correctly filtered out.
    Added exclusions for the script itself and a 'data' folder.

.EXAMPLE
    .\Copy-GitRepoContentsToClipboard.ps1
    (Run this command in the root folder of a Git repository)
#>

param (
    [string]$BasePath = (Get-Location).Path,
    [string[]]$TextFileExtensions = @(
        # Common text file extensions (all lowercase).
        # List extensions with a leading dot (e.g., ".txt", ".py").
        # List full filenames for files without extensions or specific names (e.g., "readme", ".gitignore").
        ".txt", ".ps1", ".psm1", ".psd1", ".ps1xml", # PowerShell
        ".bat", ".cmd", # Batch
        ".js", ".jsx", ".ts", ".tsx", # JavaScript/TypeScript
        ".html", ".htm", ".css", ".scss", ".less", # Web
        ".py", ".pyw", # Python
        ".java", ".cs", ".cpp", ".c", ".h", ".hpp", # C-family
        ".json", ".xml", ".yaml", ".yml", ".ini", ".config", # Config/Data
        ".md", ".log", ".csv", ".sql", ".sh", # Other common text
        ".csproj", ".vbproj", ".sln", # Project files
        ".gitignore", ".gitattributes", # Git files
        ".env", ".dockerfile", "dockerfile", "readme" # Other common files
        # Add more extensions/filenames if needed (ensure they are lowercase)
        # If this list is empty, the script will attempt to process all files from 'git ls-files'.
    ),
    [string]$SelfScriptName = "Copy-FolderContentsToClipboard.ps1", # Name of this script file to ignore
    [string]$IgnoreFolderName = "data" # Name of the folder to ignore at the repo root
)

try {
    # Check if Git is available
    try {
        Get-Command git -ErrorAction Stop | Out-Null
    } catch {
        Write-Error "Git command not found. Please ensure Git is installed and in your PATH."
        return
    }

    # Check if the current directory is a Git repository root
    if (-not (Test-Path -Path (Join-Path $BasePath ".git") -PathType Container)) {
        Write-Error "This script must be run from the root of a Git repository (a .git folder was not found)."
        return
    }

    Write-Host "Current directory is a Git repository root: $BasePath"
    Write-Host "Gathering tracked files using 'git ls-files'..."

    $gitFiles = try {
        git ls-files --exclude-standard --no-empty-directory
    } catch {
        Write-Error "Failed to execute 'git ls-files'. Error: $($_.Exception.Message)"
        return
    }
    
    if (-not $gitFiles -or $gitFiles.Length -eq 0) {
        Write-Warning "No files found tracked by Git in '$BasePath'."
        return
    }

    $allContent = [System.Text.StringBuilder]::new()
    $fileCount = 0        # Successfully read text files
    $totalSize = 0        # Total size of successfully read text files
    $processedFiles = 0   # Files considered for processing after ALL filters
    $skippedByExclusion = 0 # Files skipped due to self-ignore or data folder ignore

    Write-Host "Found $($gitFiles.Length) files/entries from git ls-files. Filtering and processing..."

    foreach ($relativeFilePathInGit in $gitFiles) {
        # Normalize path for comparison
        $normalizedRelativePath = $relativeFilePathInGit.Replace('\', '/')

        # 1. Ignore the script itself
        if ($normalizedRelativePath -eq $SelfScriptName.ToLowerInvariant()) {
            Write-Host "Skipping (self): $relativeFilePathInGit"
            $skippedByExclusion++
            continue
        }

        # 2. Ignore anything in the 'data' folder (case-insensitive) at the root
        # Paths from 'git ls-files' are relative to repo root.
        if ($normalizedRelativePath.StartsWith("$($IgnoreFolderName.ToLowerInvariant())/")) {
            Write-Host "Skipping (in ignored folder '$IgnoreFolderName'): $relativeFilePathInGit"
            $skippedByExclusion++
            continue
        }
        
        $fullFilePath = ""
        try {
            $fullFilePath = Join-Path -Path $BasePath -ChildPath $relativeFilePathInGit
        } catch {
            Write-Warning "Could not form valid path for '$relativeFilePathInGit' in base '$BasePath'. Skipping. Error: $($_.Exception.Message)"
            continue
        }
        
        $fileInfo = Get-Item -Path $fullFilePath -ErrorAction SilentlyContinue

        if (-not $fileInfo) {
            Write-Warning "File listed by git ls-files not found on disk (or access issue): $fullFilePath"
            continue
        }

        # Determine if the file is likely a text file
        $isTextFile = $false
        if ($TextFileExtensions.Count -eq 0) {
            $isTextFile = $true # Process all if no extensions specified for filtering
        } else {
            # Check if the file's full name (lowercase) is in the list (e.g., "readme", ".gitignore")
            if ($TextFileExtensions -contains $fileInfo.Name.ToLowerInvariant()) {
                $isTextFile = $true
            }

            # If not matched by full name, and the file has an extension, 
            # check if the extension (lowercase) is in the list (e.g., ".py", ".txt")
            # $fileInfo.Extension includes the leading dot, e.g., ".txt"
            if (-not $isTextFile -and $fileInfo.Extension) { 
                if ($TextFileExtensions -contains $fileInfo.Extension.ToLowerInvariant()) {
                    $isTextFile = $true
                }
            }
        }

        if (-not $isTextFile) {
            Write-Host "Skipping (filtered by extension/name list or not text): $relativeFilePathInGit"
            continue
        }
        
        $processedFiles++

        try {
            [void]$allContent.AppendLine("`n--- FILE: $relativeFilePathInGit ---`n")

            # Attempt to read with default encoding first, then UTF-8 as a fallback
            # This helps with files that might not be strictly UTF-8 but are still text.
            $content = Get-Content -Path $fullFilePath -Raw -Encoding Default -ErrorAction SilentlyContinue
            
            # Check if Get-Content failed (e.g. locked file) or returned null for a non-empty file
            if (($null -eq $content -and $fileInfo.Length -gt 0) -or (-not $?)) {
                 Write-Warning "Reading with Default encoding failed or returned empty for non-empty file: $fullFilePath. Retrying with UTF-8."
                 $content = Get-Content -Path $fullFilePath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            }
            
            if ($null -eq $content -and $fileInfo.Length -gt 0) {
                # If content is still null for a non-empty file after trying UTF-8, it's likely binary or unreadable
                Write-Warning "Could not read content for $($fullFilePath). It might be binary, an encoding issue not caught by filter, or access was denied."
                [void]$allContent.AppendLine("!!! Couldn't read content for this file. It may be binary, have an unsupported encoding, or there were access issues. !!!`n")
                continue # Skip appending this file's content
            } elseif ($null -eq $content -and $fileInfo.Length -eq 0) {
                 # File is genuinely empty
                 [void]$allContent.AppendLine("(File is empty)`n")
            }

            [void]$allContent.AppendLine($content)
            $fileCount++ 
            $totalSize += $fileInfo.Length
            Write-Host "Processed: $relativeFilePathInGit ($($fileInfo.Length) bytes)"

        } catch {
            Write-Warning "Error processing file content for $($fullFilePath): $($_.Exception.Message)"
            [void]$allContent.AppendLine("`n--- ERROR PROCESSING FILE CONTENT: $relativeFilePathInGit ---`n$($_.Exception.Message)`n")
        }
    }

    if ($allContent.Length -gt 0) {
        $allContent.ToString() | Set-Clipboard

        if ($?) { 
            Write-Host "`nSuccessfully copied content of $fileCount text files (out of $processedFiles filtered files, $skippedByExclusion excluded, total from git: $($gitFiles.Length)) ($([Math]::Round($totalSize/1KB,2)) KB) to clipboard."
        } else {
            Write-Error "Failed to copy content to clipboard. The clipboard might be locked by another application, or an unknown error occurred."
        }
    } else {
        Write-Warning "No text content was gathered from the tracked Git files (either none matched the filters, files were empty, or unreadable)."
    }

} catch {
    Write-Error "An unexpected error occurred: $($_.Exception.Message)"
    Write-Error $_.ScriptStackTrace
}

# Optional: Pause if running from explorer directly
# if ($Host.Name -eq "ConsoleHost" -and -not $PSScriptRoot) {
#     Read-Host -Prompt "Press Enter to exit"
# }
