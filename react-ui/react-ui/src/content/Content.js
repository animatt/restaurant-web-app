import React, {Component} from 'react';

class Content extends Component {
	constructor(props) {
		super(props);
	}
	render() {
		return (
			<div className="col-sm-10">
			  <main className="Content">
				<header className="App-header">
				  <h1>Welcome</h1>
				</header>
				<p>
				  Click here to make a reservation
				</p>
			  </main>
			</div>
		);
	}
}
export default Content;
