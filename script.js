document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('imageForm').addEventListener('submit', function (e) {
        e.preventDefault();  // フォームのデフォルト送信を防止

        // モーダルとスピナーを表示
        $('#imageModal').modal('show');
        document.getElementById('spinner').style.display = 'block';
        document.getElementById('generatedImage').style.display = 'none';

        // フォームデータの取得
        var userInput = document.querySelector('[name="user_input"]').value;
        var beautyMode = document.querySelector('[name="beauty_mode"]').checked;

        // 非同期リクエストの送信
        fetch('/generate_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userInput: userInput, beautyMode: beautyMode })
        })
            .then(response => response.json())
            .then(data => {
                // 画像のURLが含まれている場合、スピナーを非表示にし、画像を表示
                if (data.imageUrl) {
                    document.getElementById('spinner').style.display = 'none';
                    var imageElement = document.getElementById('generatedImage');
                    imageElement.src = data.imageUrl;
                    imageElement.style.display = 'block';
                } else {
                    // 画像生成に失敗した場合、スピナーとモーダルを非表示にする
                    document.getElementById('spinner').style.display = 'none';
                    $('#imageModal').modal('hide');
                    alert('画像生成に失敗しました。');
                }
            })
            .catch(error => {
                // エラー発生時の処理
                console.error('Error:', error);
                document.getElementById('spinner').style.display = 'none';
                $('#imageModal').modal('hide');
                alert('エラーが発生しました。');
            });
    });
});
