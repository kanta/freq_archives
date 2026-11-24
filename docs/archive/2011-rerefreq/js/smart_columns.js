//jQuery.event.add(window, "load", function(){
$(function() {
	
	var colWrap;
	var colNum;
	var colFixed;
	
	
	
	smartColumns();
	headerColumns()
	accessColumns();
	
	$(window).resize(function () {
		smartColumns();
		headerColumns()
		artistColumns();
		accessColumns();
	});
	
	jQuery.event.add(window, "load", function(){
		artistColumns();
	});
	
	
	function smartColumns() {
		
		

		$("#container").css({ 'width' : "100%"});

//		console.log($("body").width(),$("#container").innerWidth());
		
		colWrap = $("#container").innerWidth();
//		var colMargin = $(".subContainer").margin();
		colNum = Math.floor(colWrap / 320);
		colNum = Math.max(colNum, 1);
		colFixed = Math.floor(colWrap / colNum); 
		colFixed = Math.min(colFixed, 450);//maximam width
		colWrap = colFixed * colNum;
		
		
		
		
		$("#container").css({ 'width' : colWrap});
		$(".subContainer").css({ 'width' : colFixed});
//		$(".accessInner").css({ 'height' : $("#access .sectionWrapper").height()});
//		$(".subContainer.heightMax").css({ 'background' : "#ff00ff"});
		
		
	}
	
	
	function headerColumns() {
		if (colNum > 2) {
			var headerColFixed = Math.floor(colWrap / 2);
//			headerColFixedImg = Math.min(headerColFixed, 450);
			
			$(".subContainer.header.adjustable").css({ 'width' : headerColFixed});
			$(".subContainer.header.fixed").css({ 'width' : 450});
		}
	}
	
	
	function artistColumns() {
		
		$(".artistInner").css({ 'height' : "100%"});
//		console.log( $(".artistInner").eq(0).innerHeight() );
		
		if(colNum != 1) {
//			$(".artistInner").css({ 'height' : "600px"});
		
			var artistNum = $(".artistInner").size();
			var eachColNum = Math.floor(artistNum / colNum);
			var buttomColNum = artistNum % colNum;
		
			for (var i=0; i <  eachColNum; i++) {
				var innerHeight = 0;
				for (var j = 0; j < colNum; j++) {
					innerHeight = Math.max( innerHeight, $(".artistInner").eq(j + (i * colNum)).innerHeight() )
//					console.log( $(".artistInner").eq(j + (i * colNum)).innerHeight() );
				}
				for (var j = 0; j < colNum; j++) {
//					$(".artistInner:eq(j + (i * colNum))").css("height", innerHeight + "px");					
					$(".artistInner").eq(j + (i * colNum)).css("height", innerHeight + "px");
//					console.log(innerHeight, j + (i * colNum));
				}
			}
			
			var innerHeight = 0;
			for (var i=0; i < (artistNum % colNum); i ++) {
				innerHeight = Math.max( innerHeight, $(".artistInner").eq(i + (eachColNum * colNum)).innerHeight() )
			}
			for (var i=0; i < (artistNum % colNum); i ++) {
				$(".artistInner").eq(i + (eachColNum * colNum)).css("height", innerHeight + "px");
			}
		}
	
	}
	
	function accessColumns() {
		if(colNum != 1) {
		
			var accessNum = $(".accessInner").size();
			var innerHeight = 0
			for (var i=0; i < accessNum; i++) {
				innerHeight = Math.max( innerHeight, $(".accessInner").eq(i).innerHeight() )
			}
			$(".accessInner").css({ 'height' : innerHeight});
		}
	
		
	}
	
});