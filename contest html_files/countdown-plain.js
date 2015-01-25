function CountdownPlain(source, time, callback, type) {
	if (!type) type = CountdownPlain.Long;
	var start = new Date().getTime();
	var end = start + (time * 1000);
	var stop = false, running = true;

	var source = $(source);

	function update() {
		if (stop) return;
		var diff = end - new Date().getTime();
		if (diff <= 1000) {
			if (callback) {
				var result = callback(source);
				if (result) source.html(result);
				running = false;
			}
			return;
		}
		diff = Math.floor(Math.abs(diff * 0.001));
		source.html(type(diff));
		setTimeout(update, 1000);
	};

	this.stop = function() {
		stop = true;
	};

	this.setTime = function(time) {
		start = new Date().getTime();
		end = start + (time * 1000);
		if (!running) update();
	};
	update();
};
CountdownPlain.Long = function(time) {

	function pluralise(value) {
		return value == 1 ? '' : 's';
	};
	
	var hours = Math.floor(time / 3600);
	var mins = Math.floor((time / 60) % 60);
	var secs = Math.floor(time % 60);
	var result = [];
	if (hours > 0) result.push(hours + ' hour' + pluralise(hours));
	if (mins > 0) result.push(mins + ' min' + pluralise(mins));
	if (secs > 0) result.push(secs + ' sec' + pluralise(secs));
	return result.join(' ');
};
CountdownPlain.Short = function(time) {
	var hours = Math.floor(time / 3600);
	var mins = Math.floor((time / 60) % 60);
	var secs = Math.floor(time % 60);
	function pad(val) {
		if (val < 10) return '0' + val;
		else return val;
	}
	return hours + ":" + pad(mins) + ":" + pad(secs);
};