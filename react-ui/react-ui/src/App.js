import React, { Component } from 'react';
import './App.css';

import Navbar from './navbar/Navbar';
import Content from './content/Content';

class App extends Component {
	render() {
		return (
			<div className="App">
			  <Navbar />
			  <Content />
			  {/* <header className="App-header">
				  <h1>Welcome</h1>
				  </header>
				  <p>
				  Click here to make a reservation
				  </p> */}
			</div>
		);
	}
}

export default App;
