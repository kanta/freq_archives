$(function(){
   // #で始まるアンカーをクリックした場合に処理
   $('a[href^=#]').click(function() {
		// スクロールの速度
		
		// アンカーの値取得
		var href= $(this).attr("href");
		// 移動先を取得
		var target = $(href == "#" || href == "" ? 'html' : href);
		
		var targetPosition = target.offset().top;
		
		var nowPosition = $($.browser.safari ? 'body' : 'html').scrollTop();
		
		if(jQuery.browser.msie && parseInt(jQuery.browser.version) == 8){
		
			targetPosition += nowPosition;
				if (href == "#" || href == "") {
					targetPosition = 0;
				}
		}
		
		var speed = (Math.abs(nowPosition - targetPosition))/5;// ミリ秒
//		console.log(target, targetPosition, $.browser, nowPosition, speed);
		
		// スムーススクロール
		$($.browser.safari ? 'body' : 'html').animate({scrollTop:targetPosition}, speed, 'swing');
		return false;
   });
});