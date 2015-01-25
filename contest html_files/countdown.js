function Countdown(secsleft, endtext) {
	this.end = new Date().getTime() + (secsleft * 1000);
	this.id = Countdown.nextid++;
	this.complete = false;
	if (!endtext) endtext = 'Time up!';
	
	this.draw = function(element) {
		if(element)
			$(""+element+"").html(this.get());
		else {
			document.write(this.get());
		}
		this.update();
	}
	
	this.get = function() {
		var out = '';
		out += '<div class="countdown" id="countdown_'+this.id+'">';
		out += '<span class="digits" id="hours_'+this.id+'">00</span>:'
		out += '<span class="digits" id="mins_'+this.id+'">00</span>:';
		out += '<span class="digits" id="secs_'+this.id+'">00</span>';
		out += '</div>';
		return out;
	}
	
	this.update = function() {
		if (this.complete) return;
		var s = Math.floor((this.end - new Date().getTime()) * 0.001);
		if (s > 0) {
			var hours = Math.floor(s / 3600);
			s -= hours*3600;
			var mins = Math.floor(s / 60);
			s -= mins*60;
			
			hourSpan = document.getElementById('hours_'+this.id);
			minSpan = document.getElementById('mins_'+this.id);
			secsSpan = document.getElementById('secs_'+this.id);
			
			if (hourSpan) hourSpan.innerHTML = padZeros(hours,2);
			if (minSpan) minSpan.innerHTML = padZeros(mins,2);
			if (secsSpan) secsSpan.innerHTML = padZeros(s,2);
		} else {
			document.getElementById('countdown_'+this.id).innerHTML = endtext; 
			this.complete = true;
		}
	}
}

Countdown.nextid = 1;
Countdown.countdowns = new Array();
Countdown.make = function(secsleft, endtext) {
	var c = new Countdown(secsleft, endtext);
	Countdown.countdowns.push(c);
	return c;
}
Countdown.tickAll = function() {
	for (var i in Countdown.countdowns)
		if (Countdown.countdowns[i] && Countdown.countdowns[i].update)
			Countdown.countdowns[i].update();
	setTimeout(Countdown.tickAll,1000);
}